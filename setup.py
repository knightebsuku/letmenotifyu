from distutils.core import setup
import py2exe
if __name__=='__main__':
    setup(name='letmenotifyu',
          version='1.8.0',
          description='Program to notify users of new movie and series episode release from www.primewrire.ag',
          author='Lunga Mthembu (zeref)',
          author_email='zerefs@gmail.com',
          url='https://github.com/zerefs/letmenotifyu',
          license='GPL',
          scripts=['letmenotifyu'],
          packages=['notifylib'],
          data_files=[('share/applications',['ui/letmenotifyu.desktop']),('share/letmenotifyu',['ui/about7.glade','ui/confirm7.glade','ui/input7.glade', 'ui/main7.glade','ui/stats7.glade','ui/error.glade','ui/preferences.glade']), ('share/letmenotifyu',['ui/letmenotifyu.png','ui/letmenotifyu.xpm'])]
                      
          )
            





