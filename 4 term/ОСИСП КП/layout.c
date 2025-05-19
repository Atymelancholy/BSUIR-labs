#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <xkbcommon/xkbcommon.h>
#include "layout.h"
#include "utils.h"

int detect_word_layout(const wchar_t *text, int system_layout) {
    if (text == NULL || *text == L'\0') {
        wprintf(L"Empty text in detect_word_layout\n");
        return 0;
    }

    int en_count = 0;
    int ru_count = 0;
    int total_chars = 0;

    for (size_t i = 0; text[i]; i++) {
        wprintf(L"Processing char: %lc (U+%04X)\n", text[i], (unsigned int)text[i]);
        if ((text[i] >= L'A' && text[i] <= L'Z') || (text[i] >= L'a' && text[i] <= L'z')) {
            total_chars++;
            en_count++;
        } else if (text[i] >= 0x0410 && text[i] <= 0x044F) {
            total_chars++;
            ru_count++;
        }
    }

    if (total_chars == 0) {
        wprintf(L"No valid characters in text\n");
        return 0;
    }

    float en_ratio = (float)en_count / total_chars;
    float ru_ratio = (float)ru_count / total_chars;

    wprintf(L"en_ratio: %.2f, ru_ratio: %.2f, system_layout: %d (%ls)\n",
            en_ratio, ru_ratio, system_layout, system_layout == 0 ? L"us" : L"ru");

    if (system_layout == 1 && ru_ratio >= 0.5) {
        return 2;
    }
    if (system_layout == 0 && en_ratio >= 0.5) {
        return 1;
    }
    if (ru_ratio >= 0.5 && en_ratio < 0.5) {
        return 2;
    }
    if (en_ratio >= 0.5 && ru_ratio < 0.5) {
        return 1;
    }

    wprintf(L"Ambiguous layout detected\n");
    return 0;
}

int get_x11_layout_group(Display *display) {
    if (!display) {
        wprintf(L"X11 display not available\n");
        return -1;
    }
    XkbStateRec xkb_state;
    if (XkbGetState(display, XkbUseCoreKbd, &xkb_state) != Success) {
        wprintf(L"Failed to get X11 keyboard state\n");
        return -1;
    }
    int group = xkb_state.group;
    wprintf(L"X11 layout group: %d (%ls)\n", group, group == 0 ? L"us" : L"ru");
    return group;
}

void sync_xkb_state(struct xkb_state *xkb_state, int group) {
    if (group >= 0) {
        wprintf(L"Syncing xkb_state to group: %d\n", group);
        xkb_state_update_mask(xkb_state, 0, 0, 0, 0, 0, group);
    }
}

int update_system_layout(Display *display, int *system_layout) {
    int new_layout = -1;
    if (display) {
        XkbStateRec xkb_state;
        if (XkbGetState(display, XkbUseCoreKbd, &xkb_state) == Success) {
            new_layout = xkb_state.group;
            wprintf(L"X11 layout group: %d (%ls)\n", new_layout, new_layout == 0 ? L"us" : L"ru");
        } else {
            wprintf(L"Failed to get X11 keyboard state\n");
        }
    }
    if (new_layout < 0) {
        new_layout = get_gsettings_layout_group();
        if (new_layout < 0) {
            new_layout = (*system_layout + 1) % 2;
            wprintf(L"Fallback: Updated system_layout: %d (%ls)\n",
                    new_layout, new_layout == 0 ? L"us" : L"ru");
        }
    }
    *system_layout = new_layout;
    return new_layout;
}