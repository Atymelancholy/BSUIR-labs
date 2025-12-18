#ifndef IO_H
#define IO_H

#include <wchar.h>
#include <stdbool.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <X11/Xlib.h>

#define UINPUT_DEVICE "/dev/uinput"
#define LAYOUT_SWITCH_DELAY 150000
#define KEY_PRESS_DELAY 15000
#define DELETE_WORD_DELAY 40000
#define LEFTARROW_KEY_CODE 105
#define BACKSPACE_KEY_CODE 14
#define LEFTSHIFT_KEY_CODE 42
#define SPACE_KEY_CODE 57
#define LEFTALT_KEY_CODE 56

struct key_map_entry {
    int key_code;
    wchar_t eng_char;
};

static const struct key_map_entry key_map[] = {
        {KEY_Q, L'q'}, {KEY_W, L'w'}, {KEY_E, L'e'}, {KEY_R, L'r'}, {KEY_T, L't'},
        {KEY_Y, L'y'}, {KEY_U, L'u'}, {KEY_I, L'i'}, {KEY_O, L'o'}, {KEY_P, L'p'},
        {KEY_A, L'a'}, {KEY_S, L's'}, {KEY_D, L'd'}, {KEY_F, L'f'}, {KEY_G, L'g'},
        {KEY_H, L'h'}, {KEY_J, L'j'}, {KEY_K, L'k'}, {KEY_L, L'l'}, {KEY_Z, L'z'},
        {KEY_X, L'x'}, {KEY_C, L'c'}, {KEY_V, L'v'}, {KEY_B, L'b'}, {KEY_N, L'n'},
        {KEY_M, L'm'}, {KEY_1, L'1'}, {KEY_2, L'2'}, {KEY_3, L'3'}, {KEY_4, L'4'},
        {KEY_5, L'5'}, {KEY_6, L'6'}, {KEY_7, L'7'}, {KEY_8, L'8'}, {KEY_9, L'9'},
        {KEY_0, L'0'}, {KEY_MINUS, L'-'}, {KEY_EQUAL, L'='}, {KEY_LEFTBRACE, L'['},
        {KEY_RIGHTBRACE, L']'}, {KEY_SEMICOLON, L';'}, {KEY_APOSTROPHE, L'\''},
        {KEY_GRAVE, L'`'}, {KEY_BACKSLASH, L'\\'}, {KEY_COMMA, L','}, {KEY_DOT, L'.'},
        {KEY_SLASH, L'/'}
};

void send_key(int fd, int keycode, int value);
void send_char(int uinput_fd, wchar_t target_char, bool is_russian, Display *display, int *system_layout, bool use_super_space);
void select_and_delete_word(int uinput_fd, int len);
void switch_layout(int uinput_fd);
int setup_uinput_device(int *uinput_fd);

#endif