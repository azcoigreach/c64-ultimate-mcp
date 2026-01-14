; Simple Hello World for C64
; Assembles with ACME or similar assembler
; Shows text and changes screen colors

* = $0801                      ; BASIC start address

; BASIC stub: 10 SYS 2064
.byte $0c,$08,$0a,$00,$9e,$20,$32,$30,$36,$34,$00,$00,$00

* = $0810                      ; Start of machine code

        lda #$00               ; Black
        sta $d021              ; Background color
        
        lda #$0e               ; Light blue
        sta $d020              ; Border color
        
        ldx #$00               ; Counter
loop:
        lda message,x          ; Load character
        beq done               ; If zero, we're done
        sta $0400,x            ; Store to screen
        lda #$01               ; White color
        sta $d800,x            ; Color RAM
        inx
        jmp loop
        
done:
        rts                    ; Return to BASIC
        
message:
        .text "HELLO FROM C64 ULTIMATE!"
        .byte $00              ; Null terminator
