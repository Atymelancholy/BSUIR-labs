#ifndef DICTIONARY_H
#define DICTIONARY_H

#include <wchar.h>
#include <stdbool.h>

#define MAX_WORD_LEN 256
#define MAX_DICT_SIZE 100000
#define DICT_FILE_ENG "english_dict.txt"
#define DICT_FILE_RUS "russian_dict.txt"

typedef struct {
    wchar_t **words;
    size_t count;
} Dictionary;

bool load_dictionary(const char *filename, Dictionary *dict);
void free_dictionary(Dictionary *dict);
bool is_in_dict(const wchar_t *word, Dictionary *dict);
void process_word(wchar_t *word, Dictionary *eng_dict, Dictionary *rus_dict, int uinput_fd, bool use_super_space, int *system_layout, Display *display, struct xkb_state *xkb_state);

#endif