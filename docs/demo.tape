# Renders docs/demo.gif. Run from the repo root: vhs docs/demo.tape
# The recorded content lives in docs/demo.sh (which reads examples/debug-report/).

Output docs/demo.gif

Set Shell "bash"
Set FontSize 17
Set Width 1000
Set Height 600
Set Padding 16
Set Theme "GitHub Dark"
Set Framerate 20

Hide
Sleep 3s
Type "clear && bash docs/demo.sh"
Enter
Show
Sleep 21s
