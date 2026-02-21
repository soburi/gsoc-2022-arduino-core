// Copyright (c) 2026 TOKITA Hiroshi
// SPDX-License-Identifier: Apache-2.0

use core::ffi::{c_char, c_double, c_int, c_long, c_uint, c_ulong, c_void, CStr};
use core::mem::size_of;
use core::ptr;

unsafe extern "C" {
    fn malloc(size: usize) -> *mut c_void;
    fn realloc(ptr: *mut c_void, size: usize) -> *mut c_void;
    fn free(ptr: *mut c_void);
    fn snprintf(s: *mut c_char, n: usize, format: *const c_char, ...) -> c_int;
}

#[inline]
fn state_mut<'a>(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
) -> Option<(&'a mut *mut c_char, &'a mut c_uint, &'a mut c_uint)> {
    if buffer.is_null() || capacity.is_null() || len.is_null() {
        None
    } else {
        // SAFETY: null is checked above and callers pass valid pointers.
        Some(unsafe { (&mut *buffer, &mut *capacity, &mut *len) })
    }
}

#[inline]
unsafe fn c_strlen(s: *const c_char) -> usize {
    if s.is_null() {
        return 0;
    }
    // SAFETY: caller ensures `s` points to a valid NUL-terminated C string.
    unsafe { CStr::from_ptr(s).to_bytes().len() }
}

#[inline]
fn first_byte(s: *const c_char) -> Option<u8> {
    if s.is_null() {
        None
    } else {
        // SAFETY: null is checked above.
        Some(unsafe { *s as u8 })
    }
}

#[inline]
unsafe fn bytes_match(
    base: *const c_char,
    offset: usize,
    pat: *const c_char,
    pat_len: usize,
) -> bool {
    // SAFETY: caller validates both ranges are readable.
    unsafe {
        let lhs = core::slice::from_raw_parts(base.add(offset).cast::<u8>(), pat_len);
        let rhs = core::slice::from_raw_parts(pat.cast::<u8>(), pat_len);
        lhs == rhs
    }
}

#[inline]
unsafe fn index_of_char_from(
    buffer: *const c_char,
    len: usize,
    target: u8,
    from: usize,
) -> Option<usize> {
    if from >= len {
        return None;
    }
    // SAFETY: caller guarantees [from, len) are readable.
    unsafe {
        let tail = core::slice::from_raw_parts(buffer.add(from).cast::<u8>(), len - from);
        tail.iter().position(|&b| b == target).map(|idx| idx + from)
    }
}

#[inline]
unsafe fn index_of_bytes_from(
    buffer: *const c_char,
    hay_len: usize,
    pat: *const c_char,
    pat_len: usize,
    from: usize,
) -> Option<usize> {
    if pat_len == 0 {
        return Some(from);
    }
    if pat_len > hay_len.saturating_sub(from) {
        return None;
    }

    // SAFETY: caller guarantees ranges are readable.
    unsafe {
        let hay = core::slice::from_raw_parts(buffer.cast::<u8>(), hay_len);
        let needle = core::slice::from_raw_parts(pat.cast::<u8>(), pat_len);
        let max_start = hay_len - pat_len;
        for i in from..=max_start {
            if &hay[i..i + pat_len] == needle {
                return Some(i);
            }
        }
        None
    }
}

#[inline]
fn index_or_minus_one(index: Option<usize>) -> c_int {
    index.map(|idx| idx as c_int).unwrap_or(-1)
}

#[inline]
fn checked_forward_search(
    buffer: *const c_char,
    len: c_uint,
    from_index: c_uint,
) -> Option<(usize, usize)> {
    if buffer.is_null() || from_index >= len {
        return None;
    }
    Some((len as usize, from_index as usize))
}

#[inline]
fn checked_match_window(
    buffer: *const c_char,
    len: c_uint,
    pat: *const c_char,
    pat_len: c_uint,
    offset: c_uint,
) -> Option<(usize, usize)> {
    if len < pat_len {
        return None;
    }
    if offset > len.saturating_sub(pat_len) {
        return None;
    }
    if buffer.is_null() || pat.is_null() {
        return None;
    }
    Some((offset as usize, pat_len as usize))
}

#[inline]
unsafe fn compare_bytes<const IGNORE_CASE: bool>(
    lhs: *const c_char,
    rhs: *const c_char,
    len: usize,
) -> c_int {
    // SAFETY: caller validates both ranges are readable.
    unsafe {
        let lhs_bytes = core::slice::from_raw_parts(lhs.cast::<u8>(), len);
        let rhs_bytes = core::slice::from_raw_parts(rhs.cast::<u8>(), len);
        for (&a, &b) in lhs_bytes.iter().zip(rhs_bytes.iter()) {
            let (x, y) = if IGNORE_CASE {
                (a.to_ascii_lowercase(), b.to_ascii_lowercase())
            } else {
                (a, b)
            };
            if x != y {
                return x as c_int - y as c_int;
            }
        }
        0
    }
}

#[inline]
unsafe fn bytes_equal<const IGNORE_CASE: bool>(
    lhs: *const c_char,
    rhs: *const c_char,
    len: usize,
) -> bool {
    // SAFETY: caller validates both ranges are readable.
    unsafe { compare_bytes::<IGNORE_CASE>(lhs, rhs, len) == 0 }
}

#[inline]
unsafe fn last_index_of_bytes_from(
    buffer: *const c_char,
    hay_len: usize,
    pat: *const c_char,
    pat_len: usize,
    from_index: usize,
) -> Option<usize> {
    if hay_len == 0 || pat_len == 0 || pat_len > hay_len {
        return None;
    }

    let from = core::cmp::min(from_index, hay_len - 1);
    if from + 1 < pat_len {
        return None;
    }

    // SAFETY: caller validates both ranges are readable.
    unsafe {
        let hay = core::slice::from_raw_parts(buffer.cast::<u8>(), hay_len);
        let needle = core::slice::from_raw_parts(pat.cast::<u8>(), pat_len);
        let max_start = core::cmp::min(from, hay_len - pat_len);
        for i in (0..=max_start).rev() {
            if &hay[i..i + pat_len] == needle {
                return Some(i);
            }
        }
        None
    }
}

#[inline]
unsafe fn count_non_overlapping_matches(
    buffer: *const c_char,
    hay_len: usize,
    pat: *const c_char,
    pat_len: usize,
) -> usize {
    // SAFETY: caller validates both ranges are readable.
    unsafe {
        let hay = core::slice::from_raw_parts(buffer.cast::<u8>(), hay_len);
        let needle = core::slice::from_raw_parts(pat.cast::<u8>(), pat_len);
        let mut count = 0usize;
        let mut pos = 0usize;
        while pos + pat_len <= hay_len {
            if &hay[pos..pos + pat_len] == needle {
                count += 1;
                pos += pat_len;
            } else {
                pos += 1;
            }
        }
        count
    }
}

#[inline]
fn compute_replaced_len(
    current_len: c_uint,
    find_len: c_uint,
    replace_len: c_uint,
    match_count: usize,
) -> Option<c_uint> {
    let match_count_i64 = i64::try_from(match_count).ok()?;
    let len_diff = replace_len as i64 - find_len as i64;
    let delta = len_diff.checked_mul(match_count_i64)?;
    let new_len_i64 = (current_len as i64).checked_add(delta)?;
    if !(0..=(c_uint::MAX as i64)).contains(&new_len_i64) {
        return None;
    }
    Some(new_len_i64 as c_uint)
}

#[inline]
unsafe fn write_replaced_bytes(
    src: *const c_char,
    src_len: usize,
    find: *const c_char,
    find_len: usize,
    replace: *const c_char,
    replace_len: usize,
    dst: *mut c_char,
    dst_capacity: usize,
) -> usize {
    // SAFETY: caller validates source ranges and destination capacity.
    unsafe {
        let src_bytes = core::slice::from_raw_parts(src.cast::<u8>(), src_len);
        let find_bytes = core::slice::from_raw_parts(find.cast::<u8>(), find_len);
        let replace_bytes: &[u8] = if replace_len == 0 {
            &[]
        } else {
            core::slice::from_raw_parts(replace.cast::<u8>(), replace_len)
        };
        let dst_bytes = core::slice::from_raw_parts_mut(dst.cast::<u8>(), dst_capacity);

        let mut src_pos = 0usize;
        let mut dst_pos = 0usize;
        while src_pos < src_len {
            if src_pos + find_len <= src_len
                && &src_bytes[src_pos..src_pos + find_len] == find_bytes
            {
                if replace_len > 0 {
                    dst_bytes[dst_pos..dst_pos + replace_len].copy_from_slice(replace_bytes);
                }
                src_pos += find_len;
                dst_pos += replace_len;
            } else {
                dst_bytes[dst_pos] = src_bytes[src_pos];
                src_pos += 1;
                dst_pos += 1;
            }
        }

        dst_bytes[dst_pos] = 0;
        dst_pos
    }
}

enum ReplaceBytesFlow {
    Return(bool),
    Proceed {
        current_len: c_uint,
        hay_len: usize,
        needle_len: usize,
        replace_len: usize,
    },
}

#[inline]
fn validate_replace_bytes(
    buffer: *mut c_char,
    current_len: c_uint,
    find: *const c_char,
    find_len: c_uint,
    replace: *const c_char,
    replace_len: c_uint,
) -> ReplaceBytesFlow {
    if current_len == 0 || find_len == 0 {
        return ReplaceBytesFlow::Return(true);
    }
    if buffer.is_null() || find.is_null() {
        return ReplaceBytesFlow::Return(false);
    }
    if replace.is_null() && replace_len != 0 {
        return ReplaceBytesFlow::Return(false);
    }

    let hay_len = current_len as usize;
    let needle_len = find_len as usize;
    if needle_len > hay_len {
        return ReplaceBytesFlow::Return(true);
    }

    ReplaceBytesFlow::Proceed {
        current_len,
        hay_len,
        needle_len,
        replace_len: replace_len as usize,
    }
}

#[inline]
fn execute_replace_bytes(
    buffer: &mut *mut c_char,
    capacity: &mut c_uint,
    len: &mut c_uint,
    find: *const c_char,
    replace: *const c_char,
    flow: &ReplaceBytesFlow,
) -> bool {
    let ReplaceBytesFlow::Proceed {
        current_len,
        hay_len,
        needle_len,
        replace_len,
    } = flow
    else {
        return false;
    };

    // SAFETY: `flow` is validated by `validate_replace_bytes`, and pointers/lengths here are coherent.
    unsafe {
        let match_count = count_non_overlapping_matches(*buffer, *hay_len, find, *needle_len);
        if match_count == 0 {
            return true;
        }

        let Some(new_len) = compute_replaced_len(
            *current_len,
            *needle_len as c_uint,
            *replace_len as c_uint,
            match_count,
        ) else {
            return false;
        };

        let scratch_size = (new_len as usize).saturating_add(1);
        let scratch_ptr = malloc(scratch_size) as *mut c_char;
        if scratch_ptr.is_null() {
            return false;
        }

        let written = write_replaced_bytes(
            *buffer,
            *hay_len,
            find,
            *needle_len,
            replace,
            *replace_len,
            scratch_ptr,
            scratch_size,
        );

        if !ensure_capacity(buffer, capacity, len, new_len) {
            free(scratch_ptr.cast());
            return false;
        }

        ptr::copy_nonoverlapping(
            scratch_ptr.cast::<u8>(),
            (*buffer).cast::<u8>(),
            written + 1,
        );
        free(scratch_ptr.cast());
        *len = new_len;
        true
    }
}

#[inline]
fn ensure_capacity(
    buffer: &mut *mut c_char,
    capacity: &mut c_uint,
    len: &mut c_uint,
    needed_len: c_uint,
) -> bool {
    if !(*buffer).is_null() && *capacity >= needed_len {
        return true;
    }

    let alloc_size = (needed_len as usize).saturating_add(1);
    // SAFETY: realloc supports a null source pointer.
    let new_buffer = unsafe { realloc((*buffer).cast(), alloc_size) as *mut c_char };
    if new_buffer.is_null() {
        return false;
    }

    *buffer = new_buffer;
    *capacity = needed_len;

    if *len > *capacity {
        *len = *capacity;
    }

    // SAFETY: buffer has capacity+1 bytes and len <= capacity.
    unsafe {
        *(*buffer).add(*len as usize) = 0;
    }

    true
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_free(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
) {
    let Some((buffer, capacity, len)) = state_mut(buffer, capacity, len) else {
        return;
    };

    if !(*buffer).is_null() {
        // SAFETY: buffer pointer comes from malloc/realloc.
        unsafe {
            free((*buffer).cast());
        }
    }

    *buffer = ptr::null_mut();
    *capacity = 0;
    *len = 0;
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_change_buffer(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    max_str_len: c_uint,
) -> bool {
    let Some((buffer, capacity, len)) = state_mut(buffer, capacity, len) else {
        return false;
    };

    ensure_capacity(buffer, capacity, len, max_str_len)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_copy_bytes(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    src: *const c_char,
    length: c_uint,
) -> bool {
    let Some((buffer, capacity, len)) = state_mut(buffer, capacity, len) else {
        return false;
    };

    if src.is_null() {
        return false;
    }

    if !ensure_capacity(buffer, capacity, len, length) {
        return false;
    }

    // SAFETY: destination has enough space. Copy ranges do not overlap when `length > 0`.
    // Writing the terminating NUL at `length` is in-bounds.
    unsafe {
        if length > 0 {
            ptr::copy_nonoverlapping(src.cast::<u8>(), (*buffer).cast::<u8>(), length as usize);
        }
        *len = length;
        *(*buffer).add(length as usize) = 0;
    }

    true
}

#[inline]
fn normalized_base(base: u8) -> u32 {
    if (2..=36).contains(&base) {
        base as u32
    } else {
        10
    }
}

#[inline]
fn write_unsigned_base(mut value: u64, base: u32, out: &mut [c_char]) -> Option<usize> {
    const DIGITS: &[u8; 36] = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let mut scratch = [0u8; 66];
    let mut count = 0usize;

    loop {
        let digit = (value % (base as u64)) as usize;
        scratch[count] = DIGITS[digit];
        count += 1;
        value /= base as u64;
        if value == 0 {
            break;
        }
    }

    if count + 1 > out.len() {
        return None;
    }

    for i in 0..count {
        out[i] = scratch[count - 1 - i] as c_char;
    }
    out[count] = 0;
    Some(count)
}

#[inline]
fn write_signed_base(value: i64, base: u32, out: &mut [c_char]) -> Option<usize> {
    if base == 10 && value < 0 {
        if out.len() < 2 {
            return None;
        }
        out[0] = b'-' as c_char;
        let magnitude = ((-(value + 1)) as u64) + 1;
        let used = write_unsigned_base(magnitude, base, &mut out[1..])?;
        Some(1 + used)
    } else {
        write_unsigned_base(value as u64, base, out)
    }
}

#[inline]
fn apply_snprintf_result(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    tmp: *const c_char,
    tmp_cap: usize,
    written: c_int,
    apply: extern "C" fn(*mut *mut c_char, *mut c_uint, *mut c_uint, *const c_char, c_uint) -> bool,
) -> bool {
    if written < 0 {
        return false;
    }

    let text_len = if (written as usize) < tmp_cap {
        written as c_uint
    } else {
        // Match C++ behavior when local buffer truncates.
        unsafe { c_strlen(tmp) as c_uint }
    };

    apply(buffer, capacity, len, tmp, text_len)
}

macro_rules! snprintf_to_copy {
    ($buffer:expr, $capacity:expr, $len:expr, $tmp_size:expr, $fmt:expr, $($arg:expr),+ $(,)?) => {{
        let mut tmp = [0 as c_char; $tmp_size];
        // SAFETY: tmp points to writable memory and format string is valid.
        let written = unsafe {
            snprintf(
                tmp.as_mut_ptr(),
                tmp.len(),
                $fmt.as_ptr().cast::<c_char>(),
                $($arg),+
            )
        };
        apply_snprintf_result(
            $buffer,
            $capacity,
            $len,
            tmp.as_ptr(),
            tmp.len(),
            written,
            arduino_string_copy_bytes,
        )
    }};
}

macro_rules! snprintf_to_concat {
    ($buffer:expr, $capacity:expr, $len:expr, $tmp_size:expr, $fmt:expr, $($arg:expr),+ $(,)?) => {{
        let mut tmp = [0 as c_char; $tmp_size];
        // SAFETY: tmp points to writable memory and format string is valid.
        let written = unsafe {
            snprintf(
                tmp.as_mut_ptr(),
                tmp.len(),
                $fmt.as_ptr().cast::<c_char>(),
                $($arg),+
            )
        };
        apply_snprintf_result(
            $buffer,
            $capacity,
            $len,
            tmp.as_ptr(),
            tmp.len(),
            written,
            arduino_string_concat_bytes,
        )
    }};
}

#[inline]
fn copy_unsigned_base_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: u64,
    base: u8,
    tmp: &mut [c_char],
) -> bool {
    let Some(text_len) = write_unsigned_base(value, normalized_base(base), tmp) else {
        return false;
    };
    arduino_string_copy_bytes(buffer, capacity, len, tmp.as_ptr(), text_len as c_uint)
}

#[inline]
fn copy_signed_base_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: i64,
    base: u8,
    tmp: &mut [c_char],
) -> bool {
    let Some(text_len) = write_signed_base(value, normalized_base(base), tmp) else {
        return false;
    };
    arduino_string_copy_bytes(buffer, capacity, len, tmp.as_ptr(), text_len as c_uint)
}

#[inline]
fn copy_single_char(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_char,
) -> bool {
    let tmp = [value, 0];
    arduino_string_copy_bytes(buffer, capacity, len, tmp.as_ptr(), 1)
}

macro_rules! define_copy_base_unsigned {
    ($fn_name:ident, $value_ty:ty, $tmp_size:expr) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $fn_name(
            buffer: *mut *mut c_char,
            capacity: *mut c_uint,
            len: *mut c_uint,
            value: $value_ty,
            base: u8,
        ) -> bool {
            let mut tmp = [0 as c_char; $tmp_size];
            copy_unsigned_base_value(buffer, capacity, len, value as u64, base, &mut tmp)
        }
    };
}

macro_rules! define_copy_base_signed {
    ($fn_name:ident, $value_ty:ty, $tmp_size:expr) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $fn_name(
            buffer: *mut *mut c_char,
            capacity: *mut c_uint,
            len: *mut c_uint,
            value: $value_ty,
            base: u8,
        ) -> bool {
            let mut tmp = [0 as c_char; $tmp_size];
            copy_signed_base_value(buffer, capacity, len, value as i64, base, &mut tmp)
        }
    };
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_copy_char(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_char,
) -> bool {
    copy_single_char(buffer, capacity, len, value)
}

define_copy_base_unsigned!(
    arduino_string_copy_unsigned_char_base,
    u8,
    1 + 8 * size_of::<u8>()
);
define_copy_base_signed!(
    arduino_string_copy_int_base,
    c_int,
    2 + 8 * size_of::<c_int>()
);
define_copy_base_unsigned!(
    arduino_string_copy_unsigned_int_base,
    c_uint,
    1 + 8 * size_of::<c_uint>()
);
define_copy_base_signed!(
    arduino_string_copy_long_base,
    c_long,
    2 + 8 * size_of::<c_long>()
);
define_copy_base_unsigned!(
    arduino_string_copy_unsigned_long_base,
    c_ulong,
    1 + 8 * size_of::<c_ulong>()
);

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_copy_float_precision(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: f32,
    decimal_places: u8,
) -> bool {
    copy_float_precision_value(buffer, capacity, len, value as c_double, decimal_places)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_copy_double_precision(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_double,
    decimal_places: u8,
) -> bool {
    copy_float_precision_value(buffer, capacity, len, value, decimal_places)
}

#[inline]
fn copy_float_precision_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_double,
    decimal_places: u8,
) -> bool {
    let precision = core::cmp::min(decimal_places as c_int, 10);
    // SAFETY: tmp points to writable memory, format string is valid.
    snprintf_to_copy!(buffer, capacity, len, 64, b"%.*f\0", precision, value)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_copy_substring(
    src_buffer: *const c_char,
    src_len: c_uint,
    left: c_uint,
    right: c_uint,
    out_buffer: *mut *mut c_char,
    out_capacity: *mut c_uint,
    out_len: *mut c_uint,
) -> bool {
    const EMPTY: [u8; 1] = [0];

    if src_buffer.is_null() {
        if src_len != 0 {
            return false;
        }
        return arduino_string_copy_bytes(
            out_buffer,
            out_capacity,
            out_len,
            EMPTY.as_ptr().cast::<c_char>(),
            0,
        );
    }

    let mut begin = left;
    let mut end = right;
    if begin > end {
        core::mem::swap(&mut begin, &mut end);
    }
    if begin >= src_len {
        return arduino_string_copy_bytes(
            out_buffer,
            out_capacity,
            out_len,
            EMPTY.as_ptr().cast::<c_char>(),
            0,
        );
    }
    if end > src_len {
        end = src_len;
    }

    let copy_len = end - begin;
    if copy_len == 0 {
        return arduino_string_copy_bytes(
            out_buffer,
            out_capacity,
            out_len,
            EMPTY.as_ptr().cast::<c_char>(),
            0,
        );
    }

    let src = src_buffer.wrapping_add(begin as usize);
    arduino_string_copy_bytes(out_buffer, out_capacity, out_len, src, copy_len)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_concat_bytes(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    src: *const c_char,
    length: c_uint,
) -> bool {
    let Some((buffer, capacity, len)) = state_mut(buffer, capacity, len) else {
        return false;
    };

    if src.is_null() {
        return false;
    }

    if length == 0 {
        return true;
    }

    let Some(new_len) = (*len).checked_add(length) else {
        return false;
    };

    if !ensure_capacity(buffer, capacity, len, new_len) {
        return false;
    }

    // SAFETY: destination has enough space and copy ranges do not overlap.
    // Writing terminating NUL at `new_len` is in-bounds.
    unsafe {
        ptr::copy_nonoverlapping(
            src.cast::<u8>(),
            (*buffer).add(*len as usize).cast::<u8>(),
            length as usize,
        );
        *len = new_len;
        *(*buffer).add(new_len as usize) = 0;
    }

    true
}

macro_rules! define_concat_base10_unsigned {
    ($fn_name:ident, $value_ty:ty, $tmp_size:expr) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $fn_name(
            buffer: *mut *mut c_char,
            capacity: *mut c_uint,
            len: *mut c_uint,
            value: $value_ty,
        ) -> bool {
            let mut tmp = [0 as c_char; $tmp_size];
            concat_unsigned_base10_value(buffer, capacity, len, value as u64, &mut tmp)
        }
    };
}

macro_rules! define_concat_base10_signed {
    ($fn_name:ident, $value_ty:ty, $tmp_size:expr) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $fn_name(
            buffer: *mut *mut c_char,
            capacity: *mut c_uint,
            len: *mut c_uint,
            value: $value_ty,
        ) -> bool {
            let mut tmp = [0 as c_char; $tmp_size];
            concat_signed_base10_value(buffer, capacity, len, value as i64, &mut tmp)
        }
    };
}

define_concat_base10_unsigned!(
    arduino_string_concat_unsigned_char,
    u8,
    1 + 8 * size_of::<u8>()
);
define_concat_base10_signed!(arduino_string_concat_int, c_int, 2 + 8 * size_of::<c_int>());
define_concat_base10_unsigned!(
    arduino_string_concat_unsigned_int,
    c_uint,
    1 + 8 * size_of::<c_uint>()
);
define_concat_base10_signed!(
    arduino_string_concat_long,
    c_long,
    2 + 8 * size_of::<c_long>()
);
define_concat_base10_unsigned!(
    arduino_string_concat_unsigned_long,
    c_ulong,
    1 + 8 * size_of::<c_ulong>()
);

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_concat_float(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: f32,
) -> bool {
    concat_float_value(buffer, capacity, len, value as c_double)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_concat_double(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_double,
) -> bool {
    concat_float_value(buffer, capacity, len, value)
}

#[inline]
fn concat_unsigned_base10_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: u64,
    tmp: &mut [c_char],
) -> bool {
    let Some(text_len) = write_unsigned_base(value, 10, tmp) else {
        return false;
    };
    arduino_string_concat_bytes(buffer, capacity, len, tmp.as_ptr(), text_len as c_uint)
}

#[inline]
fn concat_signed_base10_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: i64,
    tmp: &mut [c_char],
) -> bool {
    let Some(text_len) = write_signed_base(value, 10, tmp) else {
        return false;
    };
    arduino_string_concat_bytes(buffer, capacity, len, tmp.as_ptr(), text_len as c_uint)
}

#[inline]
fn concat_float_value(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    value: c_double,
) -> bool {
    // SAFETY: tmp points to writable memory, format string is valid.
    snprintf_to_concat!(buffer, capacity, len, 32, b"%.2f\0", value)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_compare_cstr(
    buffer: *const c_char,
    len: c_uint,
    other: *const c_char,
) -> c_int {
    if buffer.is_null() || other.is_null() {
        if let Some(first) = first_byte(other) {
            if first != 0 {
                return -(first as c_int);
            }
        }

        if len > 0 {
            if let Some(first) = first_byte(buffer) {
                return first as c_int;
            }
        }

        return 0;
    }

    // SAFETY: non-null checked above, and `other` is assumed to be a valid C string.
    unsafe {
        let other_len = c_strlen(other);
        let lhs_len = len as usize;
        let shared_len = core::cmp::min(lhs_len, other_len);

        if shared_len > 0 {
            let diff = compare_bytes::<false>(buffer, other, shared_len);
            if diff != 0 {
                return diff;
            }
        }

        if lhs_len == other_len {
            return 0;
        }

        if lhs_len < other_len {
            let rhs = *other.add(lhs_len) as u8;
            -(rhs as c_int)
        } else {
            let lhs = *buffer.add(other_len) as u8;
            lhs as c_int
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_equals_cstr(
    buffer: *const c_char,
    len: c_uint,
    other: *const c_char,
) -> bool {
    if len == 0 {
        return first_byte(other).is_none_or(|b| b == 0);
    }

    if other.is_null() {
        return first_byte(buffer).is_some_and(|b| b == 0);
    }

    arduino_string_compare_cstr(buffer, len, other) == 0
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_equals_bytes(
    buffer: *const c_char,
    len: c_uint,
    other: *const c_char,
    other_len: c_uint,
) -> bool {
    if len != other_len {
        return false;
    }
    if len == 0 {
        return true;
    }
    if buffer.is_null() || other.is_null() {
        return false;
    }

    // SAFETY: pointers are non-null and `len` bytes are readable.
    unsafe { bytes_equal::<false>(buffer, other, len as usize) }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_equals_ignore_case(
    buffer: *const c_char,
    len: c_uint,
    other: *const c_char,
    other_len: c_uint,
) -> bool {
    if len != other_len {
        return false;
    }
    if len == 0 {
        return true;
    }
    if buffer.is_null() || other.is_null() {
        return false;
    }

    // SAFETY: pointers are non-null and `len` bytes are readable.
    unsafe { bytes_equal::<true>(buffer, other, len as usize) }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_starts_with(
    buffer: *const c_char,
    len: c_uint,
    prefix: *const c_char,
    prefix_len: c_uint,
    offset: c_uint,
) -> bool {
    let Some((start, pat_len)) = checked_match_window(buffer, len, prefix, prefix_len, offset)
    else {
        return false;
    };
    // SAFETY: ranges validated above.
    unsafe { bytes_match(buffer, start, prefix, pat_len) }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_ends_with(
    buffer: *const c_char,
    len: c_uint,
    suffix: *const c_char,
    suffix_len: c_uint,
) -> bool {
    let offset = len.saturating_sub(suffix_len);
    let Some((start, pat_len)) = checked_match_window(buffer, len, suffix, suffix_len, offset)
    else {
        return false;
    };
    // SAFETY: ranges validated above.
    unsafe { bytes_match(buffer, start, suffix, pat_len) }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_index_of_char(
    buffer: *const c_char,
    len: c_uint,
    ch: c_char,
    from_index: c_uint,
) -> c_int {
    let Some((hay_len, from)) = checked_forward_search(buffer, len, from_index) else {
        return -1;
    };

    // SAFETY: buffer is non-null and [from_index, len) is readable.
    index_or_minus_one(unsafe { index_of_char_from(buffer, hay_len, ch as u8, from) })
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_index_of_bytes(
    buffer: *const c_char,
    len: c_uint,
    pat: *const c_char,
    pat_len: c_uint,
    from_index: c_uint,
) -> c_int {
    let Some((hay_len, from)) = checked_forward_search(buffer, len, from_index) else {
        return -1;
    };
    if pat.is_null() {
        return -1;
    }
    if pat_len == 0 {
        return from_index as c_int;
    }

    // SAFETY: buffer/pat are non-null and ranges are readable.
    index_or_minus_one(unsafe { index_of_bytes_from(buffer, hay_len, pat, pat_len as usize, from) })
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_last_index_of_char(
    buffer: *const c_char,
    len: c_uint,
    ch: c_char,
    from_index: c_uint,
) -> c_int {
    let Some((hay_len, from)) = checked_forward_search(buffer, len, from_index) else {
        return -1;
    };

    let needle = [ch];
    // SAFETY: buffer is non-null and from_index < len.
    index_or_minus_one(unsafe {
        last_index_of_bytes_from(buffer, hay_len, needle.as_ptr(), needle.len(), from)
    })
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_last_index_of_bytes(
    buffer: *const c_char,
    len: c_uint,
    pat: *const c_char,
    pat_len: c_uint,
    from_index: c_uint,
) -> c_int {
    if buffer.is_null() || pat.is_null() {
        return -1;
    }

    // SAFETY: buffer/pat are non-null and caller provides readable ranges.
    index_or_minus_one(unsafe {
        last_index_of_bytes_from(
            buffer,
            len as usize,
            pat,
            pat_len as usize,
            from_index as usize,
        )
    })
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_replace_char(
    buffer: *mut c_char,
    len: c_uint,
    find_ch: c_char,
    replace_ch: c_char,
) {
    if buffer.is_null() {
        return;
    }

    let find_b = find_ch as u8;
    let replace_b = replace_ch as u8;
    // SAFETY: caller owns writable storage of at least `len` bytes.
    unsafe {
        let bytes = core::slice::from_raw_parts_mut(buffer.cast::<u8>(), len as usize);
        for b in bytes.iter_mut() {
            if *b == find_b {
                *b = replace_b;
            }
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_replace_bytes(
    buffer: *mut *mut c_char,
    capacity: *mut c_uint,
    len: *mut c_uint,
    find: *const c_char,
    find_len: c_uint,
    replace: *const c_char,
    replace_len: c_uint,
) -> bool {
    let Some((buffer, capacity, len)) = state_mut(buffer, capacity, len) else {
        return false;
    };

    let flow = validate_replace_bytes(*buffer, *len, find, find_len, replace, replace_len);
    if let ReplaceBytesFlow::Return(ok) = &flow {
        return *ok;
    }

    execute_replace_bytes(buffer, capacity, len, find, replace, &flow)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_remove(
    buffer: *mut c_char,
    len: c_uint,
    index: c_uint,
    count: c_uint,
) -> c_uint {
    if buffer.is_null() || count == 0 {
        return len;
    }

    let current_len = len;
    if index >= current_len {
        return current_len;
    }

    let remaining = current_len - index;
    let remove_count = core::cmp::min(count, remaining);

    let dst = index as usize;
    let src = (index + remove_count) as usize;
    let tail = (current_len - index - remove_count) as usize;
    let new_len = current_len - remove_count;

    // SAFETY: `buffer` is non-null. Copy ranges are within the same allocation and may overlap.
    // Writing the terminating NUL at `new_len` is within bounds.
    unsafe {
        ptr::copy(buffer.add(src), buffer.add(dst), tail);
        *buffer.add(new_len as usize) = 0;
    }

    new_len
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_reverse(buffer: *mut c_char, len: c_uint) {
    if buffer.is_null() || len <= 1 {
        return;
    }

    // SAFETY: caller owns writable string storage with at least `len` bytes.
    let bytes = unsafe { core::slice::from_raw_parts_mut(buffer.cast::<u8>(), len as usize) };
    bytes.reverse();
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_string_get_bytes(
    buffer: *const c_char,
    len: c_uint,
    out: *mut u8,
    out_size: c_uint,
    index: c_uint,
) {
    if out.is_null() || out_size == 0 {
        return;
    }

    // SAFETY: `out` is writable for `out_size` bytes. If source copy is performed, source range
    // is validated by `buffer`/`index`/`len` checks below.
    unsafe {
        let out_slice = core::slice::from_raw_parts_mut(out, out_size as usize);
        if buffer.is_null() || index >= len {
            out_slice[0] = 0;
            return;
        }

        let mut copy_len = (out_size - 1) as usize;
        let max_len = (len - index) as usize;
        if copy_len > max_len {
            copy_len = max_len;
        }

        if copy_len > 0 {
            let src =
                core::slice::from_raw_parts(buffer.add(index as usize).cast::<u8>(), copy_len);
            out_slice[..copy_len].copy_from_slice(src);
        }
        out_slice[copy_len] = 0;
    }
}
