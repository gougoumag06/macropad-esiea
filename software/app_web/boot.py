import board
import digitalio
import storage

btn = digitalio.DigitalInOut(board.GP3)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP

if btn.value:
    storage.remount("/", readonly=False)
