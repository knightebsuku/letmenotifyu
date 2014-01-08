from distutils.core import setup
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
          data_files=[('share/applications',['ui/letmenotifyu.desktop']),('share/letmenotifyu',['ui/about.glade','ui/confirm.glade','ui/input.glade', 'ui/main.glade','ui/stats.glade','ui/error.glade','ui/preferences.glade']), ('share/letmenotifyu',['ui/letmenotifyu.png','ui/letmenotifyu.xpm'])]
                      
          )
            





