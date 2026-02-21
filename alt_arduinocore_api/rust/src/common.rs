// Copyright (c) 2025 TOKITA Hiroshi
// SPDX-License-Identifier: Apache-2.0

use core::ffi::c_int;

const CTYPE_EOF: c_int = -1;

unsafe extern "C" {
    fn isalnum(c: c_int) -> c_int;
    fn isalpha(c: c_int) -> c_int;
    fn isblank(c: c_int) -> c_int;
    fn iscntrl(c: c_int) -> c_int;
    fn isdigit(c: c_int) -> c_int;
    fn isgraph(c: c_int) -> c_int;
    fn islower(c: c_int) -> c_int;
    fn isprint(c: c_int) -> c_int;
    fn ispunct(c: c_int) -> c_int;
    fn isspace(c: c_int) -> c_int;
    fn isupper(c: c_int) -> c_int;
    fn isxdigit(c: c_int) -> c_int;
    fn tolower(c: c_int) -> c_int;
    fn toupper(c: c_int) -> c_int;
}

#[unsafe(no_mangle)]
pub extern "C" fn map_i32(
    x: i32, in_min: i32, in_max: i32, out_min: i32, out_max: i32
) -> i32 {
    let num = x.wrapping_sub(in_min).wrapping_mul(out_max.wrapping_sub(out_min));
    let den = in_max.wrapping_sub(in_min);
    // Note: To keep compatibility, the panic when den=0 is left as is.
    num / den.wrapping_add(out_min)
}

#[unsafe(no_mangle)]
pub extern "C" fn makeWord_w(w: u16) -> u16 {
    w
}

#[unsafe(no_mangle)]
pub extern "C" fn makeWord_hl(h: u8, l: u8) -> u16 {
    ((h as u16) << 8) | (l as u16)
}

#[inline]
fn ctype_arg(c: c_int) -> Option<c_int> {
    if c == CTYPE_EOF || (0..=255).contains(&c) {
        Some(c)
    } else {
        None
    }
}

#[inline]
fn ctype_predicate(c: c_int, pred: unsafe extern "C" fn(c_int) -> c_int) -> bool {
    match ctype_arg(c) {
        // SAFETY: ctype_arg ensures an argument value accepted by C ctype (EOF or unsigned char range).
        Some(arg) => unsafe { pred(arg) != 0 },
        None => false,
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_alnum(c: c_int) -> bool {
    ctype_predicate(c, isalnum)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_alpha(c: c_int) -> bool {
    ctype_predicate(c, isalpha)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_ascii(c: c_int) -> bool {
    (c & !0x7f) == 0
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_blank(c: c_int) -> bool {
    ctype_predicate(c, isblank)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_cntrl(c: c_int) -> bool {
    ctype_predicate(c, iscntrl)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_digit(c: c_int) -> bool {
    ctype_predicate(c, isdigit)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_graph(c: c_int) -> bool {
    ctype_predicate(c, isgraph)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_lower(c: c_int) -> bool {
    ctype_predicate(c, islower)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_print(c: c_int) -> bool {
    ctype_predicate(c, isprint)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_punct(c: c_int) -> bool {
    ctype_predicate(c, ispunct)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_space(c: c_int) -> bool {
    ctype_predicate(c, isspace)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_upper(c: c_int) -> bool {
    ctype_predicate(c, isupper)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_is_xdigit(c: c_int) -> bool {
    ctype_predicate(c, isxdigit)
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_to_ascii(c: c_int) -> c_int {
    c & 0x7f
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_to_lower(c: c_int) -> c_int {
    match ctype_arg(c) {
        // SAFETY: ctype_arg ensures an argument value accepted by C tolower (EOF or unsigned char range).
        Some(arg) => unsafe { tolower(arg) },
        None => c,
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn arduino_wchar_to_upper(c: c_int) -> c_int {
    match ctype_arg(c) {
        // SAFETY: ctype_arg ensures an argument value accepted by C toupper (EOF or unsigned char range).
        Some(arg) => unsafe { toupper(arg) },
        None => c,
    }
}
