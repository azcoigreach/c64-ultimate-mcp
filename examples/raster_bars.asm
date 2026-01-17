; RASTER BARS DEMO (ca65)
; Creates colorful horizontal bars using raster interrupts
; Demonstrates advanced VIC-II timing techniques

.segment "CODE"

; BASIC stub: 10 SYS 2064
.byte $0c,$08,$0a,$00,$9e,$20,$32,$30,$36,$34,$00,$00,$00

.org $0810                      ; Start of ML code

init:
        sei                    ; Disable interrupts
        lda #$7f              
        sta $dc0d              ; Disable CIA interrupts
        sta $dd0d
        lda $dc0d              ; Acknowledge pending
        lda $dd0d
        
        lda #$01               ; Enable raster interrupt
        sta $d01a
        
        lda #$50               ; Raster line $50
        sta $d012
        lda $d011
        and #$7f
        sta $d011
        
        lda #<irq              ; Set IRQ vector
        sta $0314
        lda #>irq
        sta $0315
        
        cli                    ; Enable interrupts
        
loop:   jmp loop               ; Main loop (let IRQ do work)

irq:    
        inc $d020              ; Change border (visual effect)
        
        ; Cycle through colors
        lda raster_line
        clc
        adc #$08
        and #$f8
        sta $d012              ; Next raster line
        
        lda color_idx
        and #$0f
        tax
        lda colors,x
        sta $d020              ; Set border color
        
        inc color_idx
        inc raster_line
        
        lda raster_line
        cmp #$f8               ; Reset at bottom
        bne skip_reset
        lda #$50
        sta raster_line
        lda #$00
        sta color_idx
skip_reset:
        
        asl $d019              ; Acknowledge interrupt
        jmp $ea31              ; Return via standard ROM routine

raster_line: .byte $50
color_idx:   .byte $00

colors:
        .byte $06,$0e,$03,$0b  ; Blue,Lt.Blue,Cyan,Lt.Grey
        .byte $0c,$0f,$01,$01  ; Grey,Lt.Grey,White,White  
        .byte $0f,$0c,$0b,$03  ; Lt.Grey,Grey,Lt.Grey,Cyan
        .byte $0e,$06,$00,$00  ; Lt.Blue,Blue,Black,Black
