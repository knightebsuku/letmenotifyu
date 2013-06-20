#!/usr/bin/python


#setup file
from distutils.core import setup

if __name__=='__main__':
    setup(name='letmenotifyu',
          version='1.5.0',
          description='Program to notify users of new movie and series episode release from www.1channel.ch',
          author='Lunga Mthembu (zeref)',
          author_email='zerefs@gmail.com',
          url='https://github.com/zerefs/letmenotifyu',
          license='GPL',
          scripts=['letmenotifyu'],
          packages=['notifylib'],
          data_files=[('share/applications',['ui/letmenotifyu.desktop']),('ui',['ui/about.glade','ui/confirm.glade','ui/inputDialog.glade', 'ui/main.glade']), ('ui',['ui/letmenotifyu.png','ui/letmenotifyu.xpm'])]
                      
          )
            





