// FC-EXPSYNTH stage 1: serve a fixed 6502 program as the cartridge ROM (VRC6 pulse 1, ~440 Hz).
// Pin map (see schematic): A0-A14 = GPIO1..15, M2 = GPIO16, R/W = GPIO17, /ROMSEL = GPIO18,
// D0-D7 = GPIO19..26 (through 330R + 74AHCT245), EN_N = GPIO27 (low = enable the 245 output).
// Not yet run on hardware. Measure with a logic analyzer: address -> D output -> M2 falling edge.
#include <stdint.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/vreg.h"
#include "hardware/structs/sio.h"
#include "hardware/clocks.h"

#define A_SHIFT   1                 // A0 = GPIO1
#define D_SHIFT   19                // D0 = GPIO19
#define D_MASK    (0xFFu << D_SHIFT)
#define EN_N_PIN  27
#define OVERCLOCK 0                 // set 1 to try 250 MHz (check the 245 and flash timing first)

static uint32_t rom[0x8000];        // entry = byte << D_SHIFT, index = CPU address - $8000

static void build_image(void) {
    for (int i = 0; i < 0x8000; i++) rom[i] = (uint32_t)0xEA << D_SHIFT;           // NOP fill
    static const uint8_t prog[] = {
        0x78, 0xD8, 0xA2, 0xFF, 0x9A,          // C000 SEI CLD LDX #$FF TXS
        0xA9, 0x00, 0x8D, 0x03, 0x90,          // C005 LDA #$00 STA $9003
        0xA9, 0x4F, 0x8D, 0x00, 0x90,          // C00A LDA #$4F STA $9000  (duty 4, volume 15)
        0xA9, 0xFD, 0x8D, 0x01, 0x90,          // C00F LDA #$FD STA $9001  (period 253, about 440 Hz)
        0xA9, 0x80, 0x8D, 0x02, 0x90,          // C014 LDA #$80 STA $9002  (enable)
        0x4C, 0x19, 0xC0,                      // C019 JMP $C019
    };
    for (unsigned i = 0; i < sizeof prog; i++) rom[0x4000 + i] = (uint32_t)prog[i] << D_SHIFT;
    const unsigned vec[3] = {0x7FFA, 0x7FFC, 0x7FFE};    // NMI, RESET, IRQ -> $C000
    for (int k = 0; k < 3; k++) {
        rom[vec[k]]     = (uint32_t)0x00 << D_SHIFT;
        rom[vec[k] + 1] = (uint32_t)0xC0 << D_SHIFT;
    }
}

static void __no_inline_not_in_flash_func(bus_loop)(void) {
    for (;;) {
        uint32_t in  = sio_hw->gpio_in;                         // GPIO0..31 in one read
        uint32_t out = rom[(in >> A_SHIFT) & 0x7FFF];           // A0-A14 -> byte (pre-shifted)
        sio_hw->gpio_togl = (sio_hw->gpio_out ^ out) & D_MASK;  // update D0-D7 only
    }
}

int main(void) {
#if OVERCLOCK
    vreg_set_voltage(VREG_VOLTAGE_1_20);
    sleep_ms(10);
    set_sys_clock_khz(250000, true);
#endif
    build_image();
    gpio_init(EN_N_PIN); gpio_put(EN_N_PIN, 1); gpio_set_dir(EN_N_PIN, GPIO_OUT);   // 245 disabled
    for (int g = 1; g <= 18; g++) { gpio_init(g); gpio_set_dir(g, GPIO_IN); gpio_disable_pulls(g); }
    for (int g = 19; g <= 26; g++) { gpio_init(g); gpio_put(g, 0); gpio_set_dir(g, GPIO_OUT); }
    multicore_launch_core1(bus_loop);
    sleep_ms(200);                                              // loop is running
    gpio_put(EN_N_PIN, 0);                                      // enable U13; then press the console RESET button
    for (;;) tight_loop_contents();
}
