import re
from collections import defaultdict
from proto import *

class DotDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(DotDict, *args, **kwargs)
        self.__dict__ = self
    def __getattr__(self, attr):
        return self.__dict__[attr]


def VariantScene(scenes, varname, defaultvalue, audio=False):
	scene = Scene(tracks=[
			VisualTrack(
                content=ImageProvider(type=ImageProvider.scenebased,
                	sceneview=SceneView(type=SceneView.variant,
                		variable=StringVariable(type=StringVariable.map, key=varname, defaultvalue=defaultvalue),
                		variants=[SceneViewVariant(key=k,scenes=[s]) for k, s in scenes.items()])))
			])

	if audio:
		scene.audio.CopyFrom(Audio(audiotracks=[
			AudioTrack(type=AudioTrack.scenebased,
				sv=SceneView(type=SceneView.variant,
                		variable=StringVariable(type=StringVariable.map, key=varname, defaultvalue=defaultvalue),
                		variants=[SceneViewVariant(key=k,scenes=[s]) for k, s in scenes.items()]))]))
	return scene


def TemplateVariable(template):
	regex = re.compile(r'\${(.*?)}')
	match = regex.finditer(template)
	prev = None

	V = var = StringVariable()

	if not regex.search(template):
		var.type = StringVariable.constant
		var.value = template
		return var

	for m in match:

		var.type = StringVariable.add

		if m.start() and not prev:
			prev = re.match("", "") # to make prev.end() return 0

		if (prev and m.start() != prev.end()):
			var.variable1.type = StringVariable.constant
			var.variable1.value = template[prev.end():m.start()]
			var.variable2.type = StringVariable.add
			var.variable2.variable1.type = StringVariable.map
			var.variable2.variable1.key = m.group(1)
			var.variable2.variable1.defaultvalue = m.group(1)
			var = var.variable2.variable2
		else:
			var.variable1.type = StringVariable.map
			var.variable1.key = m.group(1)
			var.variable1.defaultvalue = m.group(1)
			var = var.variable2

		prev = m

	if prev.end() != len(template):
		var.type = StringVariable.constant
		var.value = template[prev.end():]
	else:
		var.type = StringVariable.constant
		var.value = ""
	return V

if __name__ == '__main__':
#	print TemplateVariable("${subject} foo ${verb} is a ${object}")
#	print TemplateVariable("${subject} ${verb} is a ${object}")
#	print TemplateVariable("quick brown fox junpps over dog ${xxx}")
	print TemplateVariable("${club}: 'We're delighted to get the deal over the line, a real statement of intent'")
