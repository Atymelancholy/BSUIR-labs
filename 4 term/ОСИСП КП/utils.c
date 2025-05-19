#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <string.h>
#include "utils.h"

const wchar_t eng_chars[] = L"qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~";
const wchar_t rus_chars[] = L"йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё";

void convert_layout(const wchar_t *input, wchar_t *output, bool to_russian) {
    size_t len = wcslen(input);
    for (size_t i = 0; i < len; i++) {
        const wchar_t *pos;
        if (to_russian) {
            pos = wcschr(eng_chars, input[i]);
            output[i] = pos ? rus_chars[pos - eng_chars] : input[i];
        } else {
            pos = wcschr(rus_chars, input[i]);
            output[i] = pos ? eng_chars[pos - rus_chars] : input[i];
        }
    }
    output[len] = L'\0';
}

int get_gsettings_layout_group() {
    FILE *pipe = popen("gsettings get org.gnome.desktop.input-sources current", "r");
    if (!pipe) {
        wprintf(L"Failed to run gsettings\n");
        return -1;
    }
    char buffer[256];
    if (fgets(buffer, sizeof(buffer), pipe)) {
        int group = atoi(buffer);
        wprintf(L"gsettings layout group: %d (%ls)\n", group, group == 0 ? L"us" : L"ru");
        pclose(pipe);
        return group;
    }
    pclose(pipe);
    return -1;
}