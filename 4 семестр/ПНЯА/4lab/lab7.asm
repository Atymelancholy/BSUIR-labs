.model small
.stack 100h
.data
sumbl db 1 dup(0)
argc dw 0
maxcmdsize equ 125
cmd_length dw ?
cmd_line db maxcmdsize+2,?,maxcmdsize dup(?)
buf db maxcmdsize+2,?,maxcmdsize dup('$')  
filename db 126 dup("$")
progname db 126 dup("$")
StringNumber db 0 
localsize db 0
StringFileOpenMsg db "File was opened ", 13,10, "$"
StringFileCloseMsg db "File was closed ", 13,10, "$"
StringErrorComandLineMsg db "Comand Line Error size",13,10,"$"
StringFileErrorOpenMsg db "File Error Open", 13,10, "$"
StringFileErrorCloseMsg db "File Error Close", 13,10, "$"
StringErrorAllocatedMsg db "Error allocated memory", 13,10, "$"
StringErrorStartMsg db "Error start other program", 13,10, "$"
StringErrorCMDMsg db "CMD line is empty", 13,10,"$"
StringBeginMsg db "The program has begun ", 13,10, "$"
StringErrorParsMsg db "Error pars params in comand line",13,10,"$" 
StringErrorOwerflowMsg db "Error Owerflow of size: size your entered bigger then 255",13,10,"$"
StringEndMsg db "The program has end ", 13,10, "$"
StringNewStr db 13,10,"$"

EPB dw 0
    dw offset line,0
    dw 005Ch,0,006Ch,0
line db 125
     db "/?"
command_text db 122 dup(?)
dsize=$-sumbl         
    
.code
Print_str macro msg
    push ax
    push dx
    mov ah,9
    mov dx,offset msg
    int 21h
    pop dx
    pop ax
endm 

Makeparams proc
    push si
    push di
    push dx
    push cx
    push bx
    xor si,si
    xor di,di   
sravn:    
    cmp cmd_line[si],' '
    jne nextstep
    call SkipSpaces
    inc argc
    cmp argc,2
    je second
    cmp argc,3
    je third
    cmp argc,4
    je forth
nextstep:
    mov dl,cmd_line[si]
    mov buf[di],dl
    inc di
    inc si
    xor dx,dx
    mov dx,cmd_length
    cmp si,dx
    jne sravn
    jmp forth 
second:
    mov cx,di
    xor di,di
secondcycle:
    xor dx,dx
    mov dl,buf[di]
    mov filename[di],dl
    mov buf[di],"$"
    inc di
    loop secondcycle
    mov filename[di],0
    xor di,di
    jmp sravn
third:
    mov cx,di
    xor di,di
thirdcycle:
    cmp buf[di],30h
    jl ErrorEnded2
    cmp buf[di],39h
    jg ErrorEnded2
    push ax
    xor ax,ax
    mov bx,10
    mov al,localsize
    mul bx
    mov localsize,al
    pop ax
    jc ErrorEnded1
    push ax
    xor ax,ax
    mov al,buf[di]
    mov buf[di],"$"
    sub al,30h
    add localsize,al
    pop ax
    jc ErrorEnded1
    inc di
    loop thirdcycle
    xor di,di
    jmp sravn
forth:
    mov cx,di
    xor di,di
forthcycle:
    cmp buf[di],30h
    jl ErrorEnded2
    cmp buf[di],39h
    jg ErrorEnded2
    push ax
    xor ax,ax
    mov al,StringNumber
    mul bx
    mov StringNumber,al
    pop ax
    jc ErrorEnded1
    push ax
    xor ax,ax
    mov al,buf[di]
    sub al,30h
    add StringNumber,al
    pop ax
    jc ErrorEnded1
    inc di
    loop forthcycle    
    jmp EndMakeparams    
ErrorEnded1:
    pop cx
    Print_str StringErrorOwerflowMsg
    jmp ErrorEnds        
ErrorEnded2:
    Print_str StringErrorParsMsg
ErrorEnds:
    pop bx
    pop cx    
    pop dx    
    pop si
    pop di
    jmp Exit                      
EndMakeparams:
    pop bx
    pop cx    
    pop dx    
    pop si
    pop di
    ret
Makeparams endp    
    
SkipSpaces proc
SkipCycle:    
    cmp cmd_line[si],' '
    je skip
    jmp EndSkip
skip:
    inc si
    jmp SkipCycle
EndSkip:    
    ret
SkipSpaces endp    

start:
    mov ah,4Ah
    mov bx,((csize/16)+1)+256/16+((dsize/16)+1)+256/16
    int 21h
    jc  ErrorExit0
    mov ax, @data
    mov es, ax
    
    xor cx,cx
    mov cl,ds:[80h]
    mov bx,cx
    mov si,81h
    mov di,offset cmd_line
    rep movsb
    
    mov ds,ax
    Print_str StringBeginMsg
    mov cmd_length,bx
    cmp cmd_length,0
    je  ErrorExit00

    call Makeparams    
    
    mov dx,offset filename
    mov ah,3Dh
    mov al,00h
    int 21h
    jc ErrorExit2 
    Print_str StringFileOpenMsg
    mov bx,ax
    mov di,01
    push si
    
    call Read
    ;Print_str StringNewStr
    ;Print_str progname     
    ;Print_str StringNewStr
    
    push cx
    xor cx,cx
    mov cl,localsize
MakeCycle:    
    call Run
    loop MakeCycle
    jmp Exit
ErrorExit00: 
    Print_str StringErrorCMDMsg
    jmp Exit 
ErrorExit0:
    Print_str StringErrorAllocatedMsg
    jmp Exit    
ErrorExit1:    
    Print_str StringErrorComandLineMsg
    jmp Exit
ErrorExit2:
    Print_str StringFileErrorOpenMsg
    jmp Exit
ErrorExit3:
    Print_str StringFileErrorCloseMsg
    jmp Exit
ErrorExit4:
    Print_str StringErrorStartMsg                
Exit:
    Print_str StringEndMsg    
    mov ax, 4c00h
    int 21h

Run proc
    mov     ax, 4B00h
    lea     dx, progname
    lea     bx, EPB
    int     21h
    jc ErrorExit4 
    ret
Run endp

Ended proc
    mov ah,3Eh
    int 21h
    jc ErrorExit3 
    Print_str StringNewStr
    Print_str StringFileCloseMsg
    ret
Ended endp

Read proc
    push cx
    push si
    push di
    xor si,si
    xor di,di
    mov cx,1
    jmp ReadCycle
ReadCycle0:
    pop bx     
ReadCycle:    
    mov dx,offset sumbl
    mov ah,3Fh
    int 21h
    jc ErrorExit2
    mov cx,ax
    jcxz EndRead
    cmp sumbl,13
    je ReadCycle
    cmp sumbl,10
    je IsNotLastProg
    push bx
    xor bx,bx
    mov bl,StringNumber
    dec bx
    cmp di,bx
    jl ReadCycle0
    pop bx 
    push bx
    xor bx,bx
    mov bl,sumbl
    mov progname[si],bl
    pop bx
    inc si
    jmp ReadCycle    
IsNotLastProg:
    inc di
    push bx
    xor bx,bx
    mov bl,StringNumber
    cmp di,bx
    jg  EndRead0
    cmp di,bx
    jl ReadCycle0
EndRead0:
    pop bx                 
EndRead:
    mov progname[si],0
    pop di  
    pop si
    pop cx
    call Ended
    ret
Read endp
        
csize=$-Makeparams    
end start