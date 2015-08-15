from proto import *
from util import VariantScene


def scenebased_track(scene, numframes, offset=0, opacityfunc=Function()):
    return VisualTrack(numframes=numframes,
                offset=offset,
                content=ImageProvider(type=ImageProvider.scenebased,
                                      sceneview=SceneView(type=SceneView.embedded,
                                      scenes=[scene])),
                opacityfunction=opacityfunc)


def CrossFade(scene1, scene2, duration):
    d2 = int(duration/2)

    blendover = Function(type=Function.keyframe,
             keyframes=[Point(x=0, y=0), Point(x=1, y=1)])

    return Scene(numframes=scene1.numframes+scene2.numframes, canbeempty=True,
        tracks=[
            scenebased_track(scene1, scene1.numframes-d2),

            VisualTrack(numframes=duration,
                    offset=scene1.numframes-d2,
                    content=ImageProvider(type=ImageProvider.scenebased,
                                          sceneview=SceneView(type=SceneView.embedded,
                                                       scenes=[Scene(numframes=duration, canbeempty=True,
                                                       tracks=[
        scenebased_track(scene1, d2, scene1.numframes - d2),
        scenebased_track(scene2, d2, 0, blendover)                                         
                                          ])]))),

            scenebased_track(scene2, scene2.numframes-d2, scene1.numframes + duration)

        ])

if __name__ == '__main__':
    from api import Connection

    APIKEY = "8885898521df3e7173ca45051ee4abbbb3926389"
    APISECRET = "edd5b1351c35fe69a0d4de55ca7f27fb96b740a7"

    scene1 = Scene(numframes=100, tracks=[
        VisualTrack(content=ImageProvider(type=ImageProvider.emptyimage, numframes=100,
            width=640, height=360, color=Color(red=255, alpha=255)))
        ])

    scene2 = Scene(numframes=100, tracks=[
        VisualTrack(content=ImageProvider(type=ImageProvider.emptyimage, numframes=100,
            width=640, height=360, color=Color(green=255, alpha=255)))
        ])


    vs = VariantScene("foo", {"a": scene1, "b":scene2}, "a", True)
    print vs

    c = Connection(APIKEY, APISECRET)
    p = c.get_project_byname("ticker_demo")
    
    movie = Movie(
        params=StreamParams(
            vparams=VideoParams(width=640, height=360)),
        scenes=[vs,])
#        scenes=[scene1, transition, scene2])
    
    p.create_dynamic_movie(movie, "varx1")     
