; Simple Hello World for C64 (ca65)
; Shows text and changes screen colors

.segment "CODE"

; BASIC stub: 10 SYS 2064
.byte $0c,$08,$0a,$00,$9e,$20,$32,$30,$36,$34,$00,$00,$00

.org $0810                      ; Start of machine code

        lda #$00               ; Black
        sta $d021              ; Background color
        
        lda #$0e               ; Light blue
        sta $d020              ; Border color
        
        ; Clear first line
        ldy #$00
clear:
        lda #$20               ; space
        sta $0400,y
        lda #$01               ; white color
        sta $d800,y
        iny
        cpy #40
        bne clear

        ldx #$00               ; Counter for message
loop:
        lda message,x          ; Load PETSCII/ASCII character
        beq done               ; If zero, we're done
        
        ; Convert uppercase letters A-Z to screen codes (1-26)
        cmp #'A'
        bcc store
        cmp #'Z'+1
        bcs store
        sec
        sbc #$40               ; A(65)->1, Z(90)->26

store:
        sta $0400,x            ; Store to screen
        lda #$01               ; White color
        sta $d800,x            ; Color RAM
        inx
        jmp loop
        
done:
        rts                    ; Return to BASIC
        
message:
        .byte "HELLO FROM C64 ULTIMATE!", $00
