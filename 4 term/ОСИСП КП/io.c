#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include "io.h"
#include "utils.h"
#include "layout.h"


void send_key(int fd, int keycode, int value) {
    struct input_event ev = {0};
    gettimeofday(&ev.time, NULL);
    ev.type = EV_KEY;
    ev.code = keycode;
    ev.value = value;
    write(fd, &ev, sizeof(ev));
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;
    write(fd, &ev, sizeof(ev));
}

void send_char(int uinput_fd, wchar_t target_char, bool is_russian, Display *display, int *system_layout, bool use_super_space) {
    wprintf(L"send_char: target_char=%lc (U+%04X), is_russian=%d\n", target_char, (unsigned int)target_char, is_russian);

    int key_code = 0;
    if (is_russian) {
        const wchar_t *pos = wcschr(rus_chars, target_char);
        if (!pos) {
            wprintf(L"Cannot map char: %lc\n", target_char);
            return;
        }
        size_t index = pos - rus_chars;
        if (index >= wcslen(eng_chars)) {
            wprintf(L"Index out of range for char: %lc\n", target_char);
            return;
        }
        wchar_t source_char = eng_chars[index];
        for (size_t i = 0; i < sizeof(key_map) / sizeof(key_map[0]); i++) {
            if (key_map[i].eng_char == source_char) {
                key_code = key_map[i].key_code;
                wprintf(L"Mapping Russian %lc to English %lc, key_code=%d\n", target_char, source_char, key_code);
                break;
            }
        }
    } else {
        for (size_t i = 0; i < sizeof(key_map) / sizeof(key_map[0]); i++) {
            if (key_map[i].eng_char == target_char) {
                key_code = key_map[i].key_code;
                wprintf(L"Using key_code=%d for English char %lc\n", key_code, target_char);
                break;
            }
        }
    }
    if (key_code == 0) {
        wprintf(L"No key code for char: %lc\n", target_char);
        return;
    }
    wprintf(L"Sending key_code=%d\n", key_code);
    send_key(uinput_fd, key_code, 1);
    usleep(KEY_PRESS_DELAY);
    send_key(uinput_fd, key_code, 0);
    usleep(KEY_PRESS_DELAY);
}

void select_and_delete_word(int uinput_fd, int len) {
    wprintf(L"Selecting and deleting word of length %d\n", len);
    send_key(uinput_fd, LEFTSHIFT_KEY_CODE, 1);
    for (int i = 0; i < len + 1; i++) {
        send_key(uinput_fd, LEFTARROW_KEY_CODE, 1);
        usleep(KEY_PRESS_DELAY);
        send_key(uinput_fd, LEFTARROW_KEY_CODE, 0);
        usleep(KEY_PRESS_DELAY);
    }
    send_key(uinput_fd, LEFTSHIFT_KEY_CODE, 0);
    send_key(uinput_fd, BACKSPACE_KEY_CODE, 1);
    usleep(KEY_PRESS_DELAY);
    send_key(uinput_fd, BACKSPACE_KEY_CODE, 0);
    usleep(DELETE_WORD_DELAY);
}

void switch_layout(int uinput_fd) {
    send_key(uinput_fd, LEFTSHIFT_KEY_CODE, 1);
    usleep(KEY_PRESS_DELAY);
    send_key(uinput_fd, LEFTALT_KEY_CODE, 1);
    usleep(KEY_PRESS_DELAY);
    send_key(uinput_fd, LEFTALT_KEY_CODE, 0);
    usleep(KEY_PRESS_DELAY);
    send_key(uinput_fd, LEFTSHIFT_KEY_CODE, 0);
    usleep(LAYOUT_SWITCH_DELAY);
}

int setup_uinput_device(int *uinput_fd) {
    *uinput_fd = open(UINPUT_DEVICE, O_WRONLY | O_NONBLOCK);
    if (*uinput_fd < 0) {
        perror("Не удалось открыть /dev/uinput");
        return -1;
    }

    if (ioctl(*uinput_fd, UI_SET_EVBIT, EV_KEY) < 0 ||
        ioctl(*uinput_fd, UI_SET_EVBIT, EV_SYN) < 0) {
        perror("Failed to set uinput event bits");
        close(*uinput_fd);
        return -1;
    }
    for (int i = 0; i < 256; ++i) {
        ioctl(*uinput_fd, UI_SET_KEYBIT, i);
    }

    struct uinput_user_dev uidev = {0};
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "virtual-keyboard");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1234;
    uidev.id.product = 0xfedc;
    uidev.id.version = 1;

    if (write(*uinput_fd, &uidev, sizeof(uidev)) < 0) {
        perror("Failed to write uinput device");
        close(*uinput_fd);
        return -1;
    }
    if (ioctl(*uinput_fd, UI_DEV_CREATE) < 0) {
        perror("Failed to create uinput device");
        close(*uinput_fd);
        return -1;
    }
    sleep(1);
    return 0;
}