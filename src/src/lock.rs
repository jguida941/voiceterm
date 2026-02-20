//! Mutex lock recovery so one poisoned lock does not kill long-running sessions.

use std::sync::{Mutex, MutexGuard};

pub(crate) fn lock_or_recover<'a, T>(lock: &'a Mutex<T>, context: &str) -> MutexGuard<'a, T> {
    match lock.lock() {
        Ok(guard) => guard,
        Err(poisoned) => {
            crate::log_debug(&format!("Mutex poisoned in {context}; recovering"));
            poisoned.into_inner()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::lock_or_recover;
    use std::sync::Mutex;

    #[test]
    fn lock_or_recover_returns_normal_guard_when_not_poisoned() {
        let lock = Mutex::new(10);
        let mut guard = lock_or_recover(&lock, "normal");
        *guard += 5;
        drop(guard);

        let value = match lock.lock() {
            Ok(guard) => guard,
            Err(_) => panic!("lock should not be poisoned"),
        };
        assert_eq!(*value, 15);
    }

    #[test]
    fn lock_or_recover_recovers_from_poisoned_mutex() {
        let lock = Mutex::new(vec![1_u8, 2_u8]);
        let _ = std::panic::catch_unwind(|| {
            let _guard = match lock.lock() {
                Ok(guard) => guard,
                Err(_) => panic!("initial lock acquisition should succeed"),
            };
            panic!("intentional poisoning for recovery test");
        });
        assert!(lock.is_poisoned(), "lock should be poisoned by panic");

        let mut guard = lock_or_recover(&lock, "poisoned-test");
        guard.push(3);
        drop(guard);

        let value = match lock.lock() {
            Ok(guard) => guard,
            Err(poisoned) => poisoned.into_inner(),
        };
        assert_eq!(*value, vec![1_u8, 2_u8, 3_u8]);
    }
}
