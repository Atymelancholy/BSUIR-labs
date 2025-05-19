#ifndef UTILS_H
#define UTILS_H

#include <wchar.h>
#include <stdbool.h>
#include <X11/Xlib.h>

extern const wchar_t eng_chars[];
extern const wchar_t rus_chars[];

void convert_layout(const wchar_t *input, wchar_t *output, bool to_russian);
int get_gsettings_layout_group(void);

#endif