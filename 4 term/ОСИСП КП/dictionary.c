#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <string.h>
#include <wctype.h>
#include <X11/Xlib.h>
#include <xkbcommon/xkbcommon.h>
#include "dictionary.h"
#include "utils.h"
#include "io.h"
#include "layout.h"

bool load_dictionary(const char *filename, Dictionary *dict) {
    FILE *file = fopen(filename, "r, ccs=UTF-8");
    if (!file) {
        wprintf(L"Ошибка: Не удалось открыть файл словаря %hs\n", filename);
        return false;
    }
    dict->words = malloc(MAX_DICT_SIZE * sizeof(wchar_t*));
    if (!dict->words) {
        fclose(file);
        return false;
    }
    dict->count = 0;
    wchar_t buffer[MAX_WORD_LEN];
    while (fgetws(buffer, MAX_WORD_LEN, file) && dict->count < MAX_DICT_SIZE) {
        size_t len = wcslen(buffer);
        if (len > 0 && buffer[len-1] == L'\n') {
            buffer[len-1] = L'\0';
            len--;
        }
        if (len == 0) continue;
        dict->words[dict->count] = malloc((len + 1) * sizeof(wchar_t));
        if (!dict->words[dict->count]) {
            for (size_t i = 0; i < dict->count; i++) free(dict->words[i]);
            free(dict->words);
            fclose(file);
            return false;
        }
        wcscpy(dict->words[dict->count], buffer);
        dict->count++;
    }
    fclose(file);
    return true;
}

void free_dictionary(Dictionary *dict) {
    for (size_t i = 0; i < dict->count; i++) free(dict->words[i]);
    free(dict->words);
    dict->words = NULL;
    dict->count = 0;
}

bool is_in_dict(const wchar_t *word, Dictionary *dict) {
    for (size_t i = 0; i < dict->count; i++) {
        if (wcscmp(word, dict->words[i]) == 0) return true;
    }
    return false;
}

void process_word(wchar_t *word, Dictionary *eng_dict, Dictionary *rus_dict, int uinput_fd, bool use_super_space, int *system_layout, Display *display, struct xkb_state *xkb_state) {
    if (!word || wcslen(word) == 0) {
        wprintf(L"Empty word, skipping\n");
        return;
    }

    wprintf(L"Processing word: %ls\n", word);
    update_system_layout(display, system_layout);
    wprintf(L"System layout before processing: %d (%ls)\n", *system_layout, *system_layout == 0 ? L"us" : L"ru");

    int layout = detect_word_layout(word, *system_layout);
    const wchar_t *layout_name;
    switch (layout) {
        case 1: layout_name = L"English"; break;
        case 2: layout_name = L"Russian"; break;
        case 0:
            wprintf(L"Ambiguous or unsupported word layout, skipping\n");
            return;
        default:
            wprintf(L"Unexpected layout value, skipping\n");
            return;
    }
    wprintf(L"Detected layout: %ls\n", layout_name);

    wchar_t converted_word[MAX_WORD_LEN];
    convert_layout(word, converted_word, layout == 1);

    bool word_found = false;
    const wchar_t *target_word = NULL;
    bool target_is_russian = false;

    if (layout == 1) {
        if (is_in_dict(converted_word, rus_dict)) {
            word_found = true;
            target_word = converted_word;
            target_is_russian = true;
        }
    } else if (layout == 2) {
        if (is_in_dict(converted_word, eng_dict)) {
            word_found = true;
            target_word = converted_word;
            target_is_russian = false;
        }
    }

    if (word_found) {
        wprintf(L"Found in %ls dictionary: %ls\n", layout == 1 ? L"Russian" : L"English", target_word);
        select_and_delete_word(uinput_fd, wcslen(word));
        switch_layout(uinput_fd);
        sync_xkb_state(xkb_state, *system_layout);
        wprintf(L"Inputting word: %ls\n", target_word);
        for (size_t i = 0; i < wcslen(target_word); i++) {
            send_char(uinput_fd, target_word[i], target_is_russian, display, system_layout, use_super_space);
        }
    } else {
        wprintf(L"No match in %ls dictionary\n", layout == 1 ? L"Russian" : L"English");
    }
}