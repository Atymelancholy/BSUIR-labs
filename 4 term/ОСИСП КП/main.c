#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <sys/select.h>
#include <linux/input.h>
#include <X11/Xlib.h>
#include <xkbcommon/xkbcommon.h>
#include <locale.h>
#include <wctype.h>
#include "utils.h"
#include "dictionary.h"
#include "io.h"
#include "layout.h"

#define INPUT_DEVICE "/dev/input/event3"
#define ESC_KEY_CODE 1
#define SPACE_KEY_CODE 57
#define BACKSPACE_KEY_CODE 14
#define LEFTSHIFT_KEY_CODE 42
#define LEFTALT_KEY_CODE 56
#define LEFTMETA_KEY_CODE 125
#define MAX_WORD_LEN 256

int main() {
    setlocale(LC_ALL, "");

    bool use_super_space = false;
    FILE *gsettings_pipe = popen("gsettings get org.gnome.desktop.input-sources xkb-options", "r");
    if (gsettings_pipe) {
        char buffer[256];
        if (fgets(buffer, sizeof(buffer), gsettings_pipe)) {
            if (strstr(buffer, "win_space_toggle")) {
                use_super_space = true;
                wprintf(L"Detected Super + Space for layout switching\n");
            } else {
                wprintf(L"Using Shift + Alt for layout switching\n");
            }
        }
        pclose(gsettings_pipe);
    }

    Display *display = XOpenDisplay(NULL);
    if (display) {
        wprintf(L"X11 display initialized\n");
    } else {
        wprintf(L"Running in Wayland, X11 unavailable\n");
    }

    struct xkb_context *xkb_context = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
    if (!xkb_context) {
        wprintf(L"Ошибка: Не удалось создать xkb_context\n");
        if (display) XCloseDisplay(display);
        return 1;
    }

    const char *rules = "evdev";
    const char *model = "pc105";
    const char *layout = "us,ru";
    const char *variant = "";
    const char *options = use_super_space ? "grp:win_space_toggle" : "grp:alt_shift_toggle";
    struct xkb_rule_names names = { rules, model, layout, variant, options };
    struct xkb_keymap *xkb_keymap = xkb_keymap_new_from_names(xkb_context, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
    if (!xkb_keymap) {
        wprintf(L"Ошибка: Не удалось создать xkb_keymap\n");
        xkb_context_unref(xkb_context);
        if (display) XCloseDisplay(display);
        return 1;
    }

    struct xkb_state *xkb_state = xkb_state_new(xkb_keymap);
    if (!xkb_state) {
        wprintf(L"Ошибка: Не удалось создать xkb_state\n");
        xkb_keymap_unref(xkb_keymap);
        xkb_context_unref(xkb_context);
        if (display) XCloseDisplay(display);
        return 1;
    }

    int system_layout = get_x11_layout_group(display);
    if (system_layout < 0) {
        system_layout = get_gsettings_layout_group();
    }
    if (system_layout >= 0) {
        sync_xkb_state(xkb_state, system_layout);
    } else {
        wprintf(L"Could not determine initial layout, defaulting to us\n");
        system_layout = 0;
    }

    Dictionary eng_dict = {0}, rus_dict = {0};
    wprintf(L"Загрузка словарей...\n");
    if (!load_dictionary(DICT_FILE_ENG, &eng_dict) || !load_dictionary(DICT_FILE_RUS, &rus_dict)) {
        xkb_state_unref(xkb_state);
        xkb_keymap_unref(xkb_keymap);
        xkb_context_unref(xkb_context);
        if (display) XCloseDisplay(display);
        free_dictionary(&eng_dict);
        free_dictionary(&rus_dict);
        return 1;
    }

    int input_fd = open(INPUT_DEVICE, O_RDONLY | O_NONBLOCK);
    if (input_fd < 0) {
        perror("Не удалось открыть устройство ввода");
        xkb_state_unref(xkb_state);
        xkb_keymap_unref(xkb_keymap);
        xkb_context_unref(xkb_context);
        if (display) XCloseDisplay(display);
        free_dictionary(&eng_dict);
        free_dictionary(&rus_dict);
        return 1;
    }

    int uinput_fd;
    if (setup_uinput_device(&uinput_fd) < 0) {
        close(input_fd);
        xkb_state_unref(xkb_state);
        xkb_keymap_unref(xkb_keymap);
        xkb_context_unref(xkb_context);
        if (display) XCloseDisplay(display);
        free_dictionary(&eng_dict);
        free_dictionary(&rus_dict);
        return 1;
    }

    wprintf(L"Слушаю ввод... Нажмите ESC для выхода.\n");

    struct input_event ev;
    wchar_t word[MAX_WORD_LEN] = {0};
    int word_len = 0;
    bool shift_pressed = false;
    bool alt_pressed = false;
    bool super_pressed = false;
    fd_set read_fds;
    struct timeval tv;

    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(input_fd, &read_fds);
        tv.tv_sec = 0;
        tv.tv_usec = 10000;

        int ret = select(input_fd + 1, &read_fds, NULL, NULL, &tv);
        if (ret < 0) {
            perror("select failed");
            break;
        }
        if (ret == 0 || !FD_ISSET(input_fd, &read_fds)) continue;

        if (read(input_fd, &ev, sizeof(ev)) != sizeof(ev)) continue;

        if (ev.type == EV_KEY && ev.value == 1) {
            if (ev.code == LEFTSHIFT_KEY_CODE) {
                shift_pressed = true;
            } else if (ev.code == LEFTALT_KEY_CODE) {
                alt_pressed = true;
            } else if (ev.code == LEFTMETA_KEY_CODE) {
                super_pressed = true;
            } else if (ev.code == ESC_KEY_CODE) {
                wprintf(L"ESC нажат. Выход.\n");
                break;
            } else if (ev.code == SPACE_KEY_CODE) {
                if (word_len > 0) {
                    word[word_len] = L'\0';
                    process_word(word, &eng_dict, &rus_dict, uinput_fd, use_super_space, &system_layout, display, xkb_state);
                    word_len = 0;
                    memset(word, 0, sizeof(word));
                }
                send_key(uinput_fd, SPACE_KEY_CODE, 1);
                send_key(uinput_fd, SPACE_KEY_CODE, 0);
                wprintf(L"Space pressed, processed word\n");
            } else if (ev.code == BACKSPACE_KEY_CODE) {
                if (word_len > 0) {
                    word[--word_len] = L'\0';
                    wprintf(L"Backspace pressed, removed last char, word_len: %d\n", word_len);
                }
            } else {
                update_system_layout(display, &system_layout);
                wprintf(L"System layout before adding char: %d (%ls)\n", system_layout, system_layout == 0 ? L"us" : L"ru");

                wchar_t c = L'\0';
                bool found = false;
                for (size_t i = 0; i < sizeof(key_map) / sizeof(key_map[0]); i++) {
                    if (key_map[i].key_code == ev.code) {
                        c = key_map[i].eng_char;
                        found = true;
                        break;
                    }
                }
                if (found && word_len < MAX_WORD_LEN - 1) {
                    if (system_layout == 1) {
                        const wchar_t *pos = wcschr(eng_chars, c);
                        if (pos) {
                            c = rus_chars[pos - eng_chars];
                        }
                    }
                    if (iswalpha(c)) {
                        word[word_len++] = c;
                        wprintf(L"Added char: %lc (U+%04X), word_len: %d, system_layout: %d (%ls)\n",
                                c, (unsigned int)c, word_len, system_layout, system_layout == 0 ? L"us" : L"ru");
                    }
                }
            }

            if ((shift_pressed && alt_pressed) || (super_pressed && ev.code == SPACE_KEY_CODE && ev.value == 1)) {
                wprintf(L"Detected manual %ls, updating layout\n", use_super_space ? L"Super + Space" : L"Shift + Alt");
                update_system_layout(display, &system_layout);
                sync_xkb_state(xkb_state, system_layout);
            }
        } else if (ev.type == EV_KEY && ev.value == 0) {
            if (ev.code == LEFTSHIFT_KEY_CODE) {
                shift_pressed = false;
            } else if (ev.code == LEFTALT_KEY_CODE) {
                alt_pressed = false;
            } else if (ev.code == LEFTMETA_KEY_CODE) {
                super_pressed = false;
            }
        }
    }

    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);
    close(input_fd);
    xkb_state_unref(xkb_state);
    xkb_keymap_unref(xkb_keymap);
    xkb_context_unref(xkb_context);
    if (display) XCloseDisplay(display);
    free_dictionary(&eng_dict);
    free_dictionary(&rus_dict);
    wprintf(L"Программа завершена.\n");
    return 0;
}