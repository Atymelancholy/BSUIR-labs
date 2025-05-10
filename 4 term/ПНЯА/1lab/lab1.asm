.model small
.stack 100h
.data
    message_input     db "Enter the string: $"
    message_result    db "Your string after sorting: $"
    message_error     db "!!!-> ERROR <-!!! $"
    message_try_again db "Try again: $"
    result            db "      |---> RESULT <---| $"
    message_source    db "Your string: $"
    message_max_len   db 10,13,"Maximum length reached (200 chars), auto-sorting...$"
    endline           db 10, 13, '$'
    size equ 200
    buffer db size+3 dup('$')  
    char_count dw 0
.code

output macro str
    mov ah, 9
    lea dx, str
    int 21h
endm

putc macro char
    mov ah, 2
    mov dl, char
    int 21h
endm

start:
    mov ax, @data
    mov ds, ax
    mov es, ax
 
    mov buffer, size
    mov char_count, 0
    
    output message_input
    
input_loop:
    mov ah, 8
    int 21h
    
    cmp al, 8
    je handle_backspace
    
    cmp al, 13
    je process_input
    
 
    call validate_char
    jc input_loop
    
    cmp char_count, size
    jae max_reached
    
    putc al
    
    mov bx, char_count
    mov buffer[bx+2], al
    inc char_count
    
    jmp input_loop

handle_backspace:
    cmp char_count, 0
    je input_loop
    dec char_count
    putc 8
    putc ' '
    putc 8
    jmp input_loop

max_reached:
    output message_max_len
    mov buffer+1, size  
    mov buffer[size+2], 13 
    mov buffer[size+3], '$'
    jmp prepare_for_sort

process_input:
    cmp char_count, 0
    je input_loop
    mov bx, char_count
    mov buffer[bx+2], 13 
    mov buffer[bx+3], '$'  
    mov buffer+1, bl       
    
    cmp char_count, size
    jb check_symbols
    
prepare_for_sort:
    mov ax, 3
    int 10h  
    output message_source   
    mov ah, 9
    mov dx, offset buffer + 2
    int 21h  
    output endline
    output endline
    jmp main_loop

check_symbols:
    mov dx, 2
symbol_check_loop: 
    mov si, dx 
    cmp byte ptr buffer[si], 13
    je prepare_for_sort
    mov al, buffer[si]
    cmp al, 20h
    je valid_symbol 
    cmp al, 41h
    js show_error
    cmp al, 5Ah
    js valid_symbol
    cmp al, 61h
    js show_error
    cmp al, 7Bh
    js valid_symbol
    jmp show_error
    
valid_symbol:
    inc dx 
    jmp symbol_check_loop

show_error:
    mov ax, 3
    int 10h 
    mov ah, 9
    mov dx, offset message_error
    int 21h
    output endline
    output message_try_again
    output endline
    jmp start

main_loop:         
    xor si, si
    xor di, di
    xor ax, ax
    xor dx, dx    
    mov si, offset buffer + 2
    
first_word:         
    cmp byte ptr[si], ' ' 
    jne check_compare
    inc si
    cmp byte ptr[si], 13
    je the_end                      
    jmp first_word
     
loop_per_line:
    inc si
    cmp byte ptr[si], ' '
    je check_whitespace
    cmp byte ptr[si], 13
    jne loop_per_line        
    cmp ax, 0                
    jne main_loop
    jmp the_end 
       
check_compare:
    cmp dx, 0
    jne compare
    push si
    mov dx, 1 
    jmp loop_per_line
    
check_whitespace:
    cmp byte ptr[si+1], ' '
    je loop_per_line
    inc si
    jmp check_compare
    
compare:
    pop di
    push si
    push di
    mov cx, si
    sub cx, di
    repe cmpsb   
    dec si
    dec di
    xor bx, bx
    mov bl, byte ptr[di] 
    cmp bl, byte ptr[si] 
    jg change
    pop di
    pop si
    push si 
    jmp loop_per_line
    
change:
    inc al
    pop di
    pop si
    xor cx, cx
    xor bx, bx
    mov dx, si
    
loop1:
    dec si
    inc cx
    cmp byte ptr [si-1], ' '
    je loop1
    
loop2:
    dec si
    mov bl, byte ptr [si] 
    push bx
    inc ah
    cmp si, di
    jne loop2
    
    mov si, dx
    
loop3:
    cmp byte ptr [si], 13
    je loop4
    mov bl, byte ptr [si]
    xchg byte ptr [di], bl   
    inc si
    inc di
    cmp byte ptr [si], ' '
    jne loop3
    
loop4:
    mov byte ptr[di], ' '
    inc di
    loop loop4
    
    mov si, di
    mov dx, si
    dec si
    
loop5:
    inc si
    cmp byte ptr[si], 13
    je main_loop
    pop bx
    mov byte ptr[si], bl
    dec ah
    cmp ah, 0
    je loop6
    jmp loop5
    
loop6:
    push dx
    mov dx, 1
    xor cx, cx
    jmp loop_per_line     
           
the_end:
    output endline
    output endline   
    output endline
    output result  
    output endline
    output endline
    output message_result 
    mov ah, 9
    mov dx, offset buffer + 2
    int 21h
    jmp exit

validate_char proc
    cmp al, ' '
    je valid
    cmp al, 'A'
    jb invalid
    cmp al, 'Z'
    jbe valid
    cmp al, 'a'
    jb invalid
    cmp al, 'z'
    jbe valid
invalid:
    stc
    ret
valid:
    clc
    ret
validate_char endp

exit:    
    mov ah, 4Ch
    int 21h 
end start