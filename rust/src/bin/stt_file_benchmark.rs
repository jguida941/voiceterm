//! Strict STT-only benchmark on one WAV clip for apples-to-apples engine comparison.

use anyhow::{bail, Context, Result};
use clap::Parser;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::Instant;
use voiceterm::config::AppConfig;
use voiceterm::stt;

/// Benchmark Rust Whisper transcription on a fixed WAV file.
#[derive(Debug, Parser)]
#[command(about = "Benchmark Rust STT on one WAV file")]
struct Args {
    /// Input WAV path (recommended: mono, 16kHz)
    #[arg(long)]
    wav: PathBuf,

    /// Number of STT runs on the same WAV clip
    #[arg(long, default_value_t = 3)]
    runs: usize,

    /// Whisper model name (for config consistency)
    #[arg(long, default_value = "base.en")]
    whisper_model: String,

    /// Whisper GGML model path used by whisper-rs
    #[arg(long)]
    whisper_model_path: Option<PathBuf>,

    /// Language passed to Whisper ("auto" or ISO code)
    #[arg(long, default_value = "en")]
    lang: String,
}

fn main() -> Result<()> {
    let args = Args::parse();
    if args.runs == 0 {
        bail!("--runs must be >= 1");
    }

    let mut config = AppConfig::parse_from(Vec::<String>::new());
    config.whisper_model = args.whisper_model.clone();
    config.lang = args.lang.clone();
    if let Some(path) = &args.whisper_model_path {
        config.whisper_model_path = Some(path.to_string_lossy().to_string());
    }
    config.validate()?;

    let model_path = config
        .whisper_model_path
        .as_deref()
        .context("no whisper model path available after config validation")?;

    let (samples, sample_rate) = load_wav_mono_f32(&args.wav)?;
    if sample_rate != config.voice_sample_rate {
        bail!(
            "wav sample rate {} Hz does not match configured voice sample rate {} Hz; re-record with '-ar {}'",
            sample_rate,
            config.voice_sample_rate,
            config.voice_sample_rate
        );
    }

    let mut transcriber =
        stt::Transcriber::new(model_path).context("failed to initialize Rust transcriber")?;

    let mut run_times_ms = Vec::with_capacity(args.runs);
    let mut last_transcript = String::new();
    for _ in 0..args.runs {
        let start = Instant::now();
        let transcript = transcriber
            .transcribe(&samples, &config)
            .context("Rust transcription failed")?;
        let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
        run_times_ms.push(elapsed_ms);
        last_transcript = transcript;
    }

    let min_ms = run_times_ms.iter().copied().fold(f64::INFINITY, f64::min);
    let max_ms = run_times_ms
        .iter()
        .copied()
        .fold(f64::NEG_INFINITY, f64::max);
    let avg_ms = run_times_ms.iter().copied().sum::<f64>() / run_times_ms.len() as f64;

    println!(
        "stt_file_benchmark|engine=rust|runs={}|avg_stt_ms={:.1}|min_stt_ms={:.1}|max_stt_ms={:.1}|chars={}",
        args.runs,
        avg_ms,
        min_ms,
        max_ms,
        last_transcript.chars().count()
    );

    Ok(())
}

fn load_wav_mono_f32(path: &Path) -> Result<(Vec<f32>, u32)> {
    let bytes = fs::read(path).with_context(|| format!("failed to read '{}'", path.display()))?;
    let (channels, sample_rate, pcm_data) = parse_pcm16_wav(&bytes)
        .with_context(|| format!("unsupported wav format in '{}'", path.display()))?;
    if pcm_data.len() % 2 != 0 {
        bail!("wav pcm payload has odd byte length");
    }
    let channels = usize::from(channels.max(1));
    let total_samples = pcm_data.len() / 2;
    if total_samples < channels {
        bail!("wav pcm payload is too short for {} channels", channels);
    }

    let frame_count = total_samples / channels;
    let mut mono = Vec::with_capacity(frame_count);
    let scale = i16::MAX as f32;
    for frame_idx in 0..frame_count {
        let mut sum = 0.0f32;
        for ch in 0..channels {
            let sample_idx = frame_idx * channels + ch;
            let byte_idx = sample_idx * 2;
            let sample = i16::from_le_bytes([pcm_data[byte_idx], pcm_data[byte_idx + 1]]);
            sum += sample as f32 / scale;
        }
        mono.push(sum / channels as f32);
    }

    Ok((mono, sample_rate))
}

fn parse_pcm16_wav(bytes: &[u8]) -> Result<(u16, u32, &[u8])> {
    if bytes.len() < 12 {
        bail!("wav file is too short");
    }
    if &bytes[0..4] != b"RIFF" || &bytes[8..12] != b"WAVE" {
        bail!("not a RIFF/WAVE file");
    }

    let mut channels: Option<u16> = None;
    let mut sample_rate: Option<u32> = None;
    let mut data: Option<&[u8]> = None;

    let mut offset = 12usize;
    while offset + 8 <= bytes.len() {
        let chunk_id = &bytes[offset..offset + 4];
        let chunk_size = u32::from_le_bytes([
            bytes[offset + 4],
            bytes[offset + 5],
            bytes[offset + 6],
            bytes[offset + 7],
        ]) as usize;
        let chunk_start = offset + 8;
        let chunk_end = chunk_start.saturating_add(chunk_size);
        if chunk_end > bytes.len() {
            bail!("wav chunk exceeds file bounds");
        }

        if chunk_id == b"fmt " {
            if chunk_size < 16 {
                bail!("wav fmt chunk is too short");
            }
            let audio_format = u16::from_le_bytes([bytes[chunk_start], bytes[chunk_start + 1]]);
            let ch = u16::from_le_bytes([bytes[chunk_start + 2], bytes[chunk_start + 3]]);
            let sr = u32::from_le_bytes([
                bytes[chunk_start + 4],
                bytes[chunk_start + 5],
                bytes[chunk_start + 6],
                bytes[chunk_start + 7],
            ]);
            let bits_per_sample =
                u16::from_le_bytes([bytes[chunk_start + 14], bytes[chunk_start + 15]]);

            if audio_format != 1 {
                bail!("only PCM wav (format=1) is supported, got {}", audio_format);
            }
            if bits_per_sample != 16 {
                bail!(
                    "only PCM16 wav is supported, got {} bits per sample",
                    bits_per_sample
                );
            }
            channels = Some(ch);
            sample_rate = Some(sr);
        } else if chunk_id == b"data" {
            data = Some(&bytes[chunk_start..chunk_end]);
        }

        // RIFF chunk payloads are word-aligned.
        offset = chunk_end + (chunk_size % 2);
    }

    let channels = channels.context("missing fmt chunk")?;
    let sample_rate = sample_rate.context("missing sample rate in fmt chunk")?;
    let data = data.context("missing data chunk")?;
    Ok((channels, sample_rate, data))
}
