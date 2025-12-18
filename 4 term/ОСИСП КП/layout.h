#ifndef LAYOUT_H
#define LAYOUT_H

#include <wchar.h>
#include <X11/Xlib.h>
#include <xkbcommon/xkbcommon.h>

int detect_word_layout(const wchar_t *text, int system_layout);
int get_x11_layout_group(Display *display);
void sync_xkb_state(struct xkb_state *xkb_state, int group);
int update_system_layout(Display *display, int *system_layout);

#endif