.model small
.stack 100h
.data
    numberTen dw 000Ah
    sizeOfNumber equ 2
    maxAccuracy equ 10
    maxArrayLength equ 1Eh 
    numberStringLength equ 20  
    accuracy dw ?
    length dw ? 
    array dw maxArrayLength dup(0)                                     
    numberString db numberStringLength dup('$')
    inputLimitsString db "Max array length = 30. Max accuracy = 10. ", 0Dh, 0Ah, "Max array element value = 32767, min = -32768.$"
    invalidLengthString db "Invalid length input. 1 <= length <= 30.$"
    invalidAccuracyString db "Invalid accuracy input. 0 <= accuracy <= 10.$"
    inputLengthString db "Input array length:$" 
    inputArrayString db "Input array numbers:$" 
    inputAccuracyString db "Input accuracy:$"
    invalidInputString db "Invalid input. $" 
    overflowInputString db "Number is too big. $"
    overflowSumString db "Array sum overflow. Further work is impossible.$"
    tryAgainString db "Try again:$" 
    inputInviteString db "Enter number:$"
    newLine db 0Dh,0Ah,'$'
    minusFlag db 0
.code 

inputNumbers proc
    call printNewLine
    lea dx, inputInviteString
    call outputString
repeatElementInput:
    lea dx, numberString   
    call inputString          
    lea si, numberString[2]
    call parseString
    jc invalidInput
    call loadNumber 
    loop inputNumbers
ret

invalidInput:
    call printNewLine
    lea dx, invalidInputString
    call outputString
    jno tryAgainOutput
    lea dx, overflowInputString
    call outputString
tryAgainOutput:
    lea dx, tryAgainString
    call outputString
    jmp repeatElementInput
    
loadNumber:
    mov [di], ax
    add di, sizeOfNumber
ret 
inputNumbers endp

  
parseString proc
    xor dx, dx
    xor bx, bx
    xor ax, ax
    mov [minusFlag], 0    

    cmp byte ptr [si], 0Dh
    je invalidString
   
    cmp byte ptr [si], '-'
    jne checkPlus
    mov [minusFlag], 1
    inc si
    jmp afterSign
    
checkPlus:
    cmp byte ptr [si], '+'
    jne afterSign
    inc si
    
afterSign:
    cmp byte ptr [si], 0Dh
    je invalidString
    
parseStringLoop:
    mov bl, [si]
    
    cmp bl, 0Dh        
    je endParsing
    
    cmp bl, '0'                               
    jl invalidString     
    cmp bl, '9'
    jg invalidString     
    
    sub bl, '0'         
   
    imul word ptr [numberTen]
    jo invalidString
   
    add ax, bx
    jo invalidString
    
    inc si
    jmp parseStringLoop
    
invalidString:
    stc              
    ret
    
endParsing:
    cmp [minusFlag], 1
    jne positiveNum
    neg ax
    js checkMinRange   
    jmp done
    
positiveNum:
    cmp ax, 32767       
    ja invalidString
    
done:
    clc               
    ret
    
checkMinRange:
    cmp ax, 8000h       
    jne done
    clc
    ret
parseString endp


findArraySum proc 
    xor ax, ax
sumLoop:
    add ax, [si]
    jo overflowDetected
    add si, sizeOfNumber  
    loop sumLoop
    clc
    ret
    
overflowDetected:
    stc
    ret
findArraySum endp

numberToString proc
    push dx                    
    push 0024h         
    test ax, ax       
    js numberIsNegative  
    
quotientToStringConvertingLoop:    
    xor dx, dx        
    div word ptr [numberTen]
    add dl, '0'
    push dx
    cmp ax, 0
    jne quotientToStringConvertingLoop   
    
moveQuotientToBuffer:
    pop ax
    cmp al, '$'
    je moveRemainerToBuffer
    mov [di], al
    inc di
    jmp moveQuotientToBuffer
    
moveRemainerToBuffer:
    pop ax             
    cmp cx, 0
    je endConverting
    mov [di], '.'
    inc di    
    
remainerConvertingLoop:
    mul word ptr [numberTen]
    idiv bx           
    add al, '0'
    mov [di], al
    inc di
    mov al, ah
    xor ah, ah
    loop remainerConvertingLoop
    
endConverting:
    mov [di], '$'
    ret

numberIsNegative:
    mov [di], '-'
    inc di
    neg ax            
    jmp quotientToStringConvertingLoop 
numberToString endp    

lengthInput proc
    call printNewLine    
    lea dx, inputLengthString
    call outputString         
    lea di, length  
    mov cx, 0001h         
    call inputNumbers
    mov ax, [length]
    cmp ax, maxArrayLength
    jg invalidLengthInput
    cmp ax, 0001h
    jl invalidLengthInput     
    call printNewLine
    ret

invalidLengthInput:
    call printNewLine
    lea dx, invalidLengthString
    call outputString
    call printNewLine
    jmp lengthInput  
lengthInput endp

arrayInput proc
    call printNewLine 
    lea dx, inputArrayString
    call outputString             
    mov cx, [length]     
    lea di, array        
    call inputNumbers
    call printNewLine 
    ret
arrayInput endp

accuracyInput proc
    call printNewLine     
    lea dx, inputAccuracyString
    call outputString                          
    lea di, accuracy  
    mov cx, 0001h
    call inputNumbers
    mov ax, [accuracy]
    cmp ax, maxAccuracy
    jg invalidAccuracyInput
    cmp ax, 0000h
    jl invalidAccuracyInput     
    call printNewLine
    ret

invalidAccuracyInput:
    call printNewLine
    lea dx, invalidAccuracyString
    call outputString
    call printNewLine
    jmp accuracyInput
accuracyInput endp

findAverage proc
    mov cx, [length]
    lea si, array
    call findArraySum
    jc overflowSum
    
    mov bx, [length]
    cwd                 
    idiv bx

    mov [integerPart], ax
    mov [fractionPart], dx
    ret
    
overflowSum:
    call printNewLine
    lea dx, overflowSumString
    call outputString
    jmp exit
findAverage endp 

.data
integerPart dw ?
fractionPart dw ?

.code
printNewLine proc
    lea dx, newLine
    call outputString
    ret
printNewLine endp

outputString proc
    mov ah, 09h
    int 21h    
    ret
outputString endp

inputString proc
    mov ah, 0Ah
    int 21h
    ret
inputString endp

start:
    mov ax, @data
    mov ds, ax
    mov es, ax
    
    mov [numberString], numberStringLength
    
    lea dx, inputLimitsString
    call outputString
    call printNewLine

    call lengthInput
    call arrayInput 
    call accuracyInput    
    call findAverage
 
    mov ax, [integerPart]
    mov dx, [fractionPart]
    mov bx, [length]
    mov cx, [accuracy]
    lea di, numberString[2]
    call numberToString

    lea dx, numberString[2]
    call outputString
    
exit:    
    mov ax, 4c00h
    int 21h    
end start