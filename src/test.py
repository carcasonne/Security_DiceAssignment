command = "/commit fjdlskfjdsl"
split = command.split("/commit")
split.pop(0)
command = split[0]
command = command.strip()

print(command)