
; You may customize this and other start-up templates; 
; The location of this template is c:\emu8086\inc\0_com_template.txt

org 100h

.model small
.stack 100h
.data
          
fd dw 0                            ;descriptor faila  
  
count_str dw 0
count dw 0                            

filepath db 50 DUP(0)          ;put do fila    

word_size dw 0                     
is_end db 0                         ; exit(0)
char db 0                         

line_begining_dx dw 0              
line_begining_ax dw 0              

string db 201                       
       db ?                         
       db 201 dup('$')              
found_substr db 0                   

error_sizemsg db "Invalid passed arguments", 10, 13, '$'              
enter_msg db "Enter symbols: ", 10, 13, '$'
find_err db "Can't find file!", 10, 13, 0, '$'               
path_err db "Can't find file path!", 10, 13, 0, '$'          
toomany_err db "Too many opened files!", 10, 13, 0, '$'         
accessdenied_err db "Access denied!", 10, 13, 0, '$'           
string_err_msg db "Invalid symbols, try again: ", 10, 13, 0, '$'

.code

print macro str                            
    push ax                                
    push dx
    mov dx, offset str                     
    mov ah, 09h                            
    int 21h                             
    pop dx                              
    pop ax
endm


print_number proc 
        push    ax
        push    bx
        push    cx
        push    dx
        push    di
 
        mov     cx, 10          ; cx - base number 
        xor     di, di          ; di - digits in number
        
        cmp     ah, 0
@convert:
        xor     dx, dx
        div     cx             
        add     dl, '0'
        inc     di
        push    dx              
        or      ax, ax
        jnz     @convert
        
@display: 
        pop     dx              ; dl = symbol
        mov     ah, 02h           
        int     21h
        dec     di              ; repeat while di<>0
        jnz     @display
 
        pop     di
        pop     dx
        pop     cx
        pop     bx
        pop     ax
        ret
       
print_number endp

new_line macro
    mov dl,10
    mov ah,2
    int 21h
    mov dl,13
    mov ah,2
    int 21h
endm

changePos macro dir, newPos            
    local cnt_change, cnt_changePos     ;localnie metki dlia dannogo macrosa
    mov ah, 42h             ;functia peremeschenia ukazatelia chtenia/zapisi            
    mov al, 1           ;0 - nachalo faila 1 - tekuschaya posiciia 2 - eof                
    mov bx, fd          ; indificator faila                
    mov dx, newPos       ;cx:dx rastoianie na kotoroe nado peremestit ukazatel               
    mov cl, 0                           
    cmp cl, dir                         
    je cnt_change                       
    
    neg dx 
    mov cx, 0FFFFh 
    jmp cnt_changePos
    
    cnt_change: 
        mov cx, 0
    
    cnt_changePos: 
        int 21h
endm


openFile proc
    jmp openFile_start 
    
    cant_find_error:                
    print find_err
    mov is_end, 1
    jmp openFile_end
    
    path_error:
        print path_err
        mov is_end, 1
        jmp openFile_end
    
    toomany_error:
        print toomany_err
        mov is_end, 1
        jmp openFile_end
    
    access_error:
        print accessdenied_err
        mov is_end, 1
        jmp openFile_end
    
    openFile_start:
        mov dx, offset filepath       
        mov al, 0                     
        mov ah, 3Dh                   
        int 21h
        jc openFile_fin_err           
        mov bx, ax                    
        mov fd, bx                  
        jmp openFile_end           
    
    openFile_fin_err:           
        cmp ax, 02h             
        je cant_find_error
        cmp ax, 03h             
        je path_error
        cmp ax, 04h             
        je toomany_error
        cmp ax, 05h             
        je access_error
    
    openFile_end:
        ret
openFile endp 

handleLine proc
    call inc_count
    
    handleLine_start:
        mov ah, 42h                       
        mov al, 0                         
        mov bx, fd                    
        mov cx, line_begining_dx           
        mov dx, line_begining_ax          
        int 21h

    handleLineFor:                   
        mov bx,fd                
        mov cx,1                 
        mov ah,3Fh                   
        mov dx,offset char        
        int 21h

        cmp ax,0                     ; EOF
        je skip_eol
        mov al,10                    ; \n
        cmp al,char
        je skip_eol
        mov al,13                    ; \r
        cmp al,char   
        je skip_eol

    jmp handleLineFor

    set_end_file_0_fin:
        mov is_end,1
        jmp handleLine_fin

    skip_eol:                      
        mov bx,fd               
        mov cx,1                    
        mov ah,3Fh                  
        mov dx,offset char        
        int 21h

        cmp ax,0                    
        je set_end_file_0_fin
        
        mov al,10                   
        cmp al,char
        je skip_eol

        mov al,13
        cmp al,char
        je skip_eol
    
    changePos 1,1               
    
    handleLine_fin:
        ret
handleLine endp

checkLine proc         ;prohod po stroke i poisk symbols                         
    jmp check_start
    
    foundAllSymbols:
 
        mov count_str,0
        mov found_substr,1
        jmp checkLineEnd
        
    set_end_fin:
        mov is_end, 1
        jmp checkLineEnd    
        
    check_start:
        mov di, offset string + 2  ;zagrujaem v di adress vvedionoi stroki         
        mov is_end, 0
        mov found_substr,0

    checkLineFor: 
        mov bx, fd
        mov cx, 1
        mov ah, 3fh 
        mov dx,offset char
        int 21h

        cmp ax,0    ;esli nichego ne schitalo konec fila i vixod                  
        je set_end_fin
        
        inc count_str

        mov al,10                     ;\n
        cmp al, char
        je checkLineEnd               ;conec stroci
        mov al,13                     ;\r
        cmp al, char                
        je checkLineEnd               ;conec stroci

        mov al,[di]                   
        cmp al, char                  ;sravnivaem symvol stroci i schitanii iz fila symvol
        jne checkLineFor

        inc di                ;esli sleduuschii - symvol konc vvedionnogo slova 
        mov al,[di]
        cmp al,'$' 
        je foundAllSymbols 
        
        mov ax,4201h            ; ??????????? ????????? ????? ?? ??????? ???????                         
        mov bx, fd 
        mov dx,count_str ; ?? 5 ???? ?????, ??????? ?????????? ? ?????
        neg dx
        mov cx,-1 ; ?? ??????? ???????? ? cx:dx ?? ????????? ????????? ???? (??? 5 ?? dx) ?????? ? -1 ? ?? 
        int 21h
        
        mov count_str,0

    jmp checkLineFor

    checkLineEnd:
    mov count_str,0
    ret
checkLine endp

inc_count proc
    inc count   
    ret   
inc_count endp

countString proc                              
    push ax
    push bx
    push cx
    push dx

    checkLines:
        
        changePos 0, 1           
        mov line_begining_dx, dx
        dec ax
        mov line_begining_ax, ax
        changePos 1, 1

        call checkLine             

        cmp is_end,1                
        je countWordEnd            

        cmp found_substr, 1         
        jne checkLines

        call handleLine                     
    jmp checkLines
    
    countWordEnd:
        pop dx 
        pop cx
        pop bx
        pop ax
        new_line 
        mov ax, count
        call print_number     
        ret
countString endp

get_str_size proc               
    mov di,offset string+1     
    mov dh,0
    mov dl,[di]
    mov word_size,0
    add word_size,dx
    ret
get_str_size endp

start:
    mov ax, @data
    mov ds, ax
    
    xor cx, cx
    mov cl, es:[80h] ;?????? ?????????? ?????? ? ????? psp
    
    cmp cl, 0 
    je exit_bcsize
  
    mov si, 81h  ;???? ?????????? ??????
    xor di,di 
    
    inc si   
    dec cl   
    
    get_parm:
        mov al, byte ptr es:[si]   ; ?????? ????? ?? es:si
        mov byte ptr [filepath + di], al  ; ?????????? ?????
        inc di
        inc si
        loop get_parm

    jmp string_input
    
    exit_bcsize:
        mov ah, 9
        mov dx, offset error_sizemsg
        int 21h
        jmp exit
    
    string_error:                      
        new_line
        mov ah, 9
        mov dx, offset string_err_msg
        int 21h
        new_line
        jmp string_input
    
    string_input:                         
        mov ah, 9
        mov dx, offset enter_msg
        int 21h
        mov ah, 0Ah ;???????????????? ????
        mov dx, offset string
        int 21h                 
    
        mov si, offset string + 1
        mov cl, [si]
        mov ch, 0
        cmp cx, 0
        je  string_error ;???? ?? ???? ??????
        inc cx
        add si, cx
        mov al, '$'
        mov [si], al
    
    call get_str_size
    
    call openFile
    cmp is_end, 1
    je exit
    
    call countString
        
    close_file:
        mov ah, 3Eh                 
        mov bx, fd
        int 21h 
        
    exit:
        mov ax, 4C00h
        int 21h
end start


ret




