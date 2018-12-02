# -*- mode: python -*-

block_cipher = None


a = Analysis(['manas.py'],
             pathex=['D:\\py\\manazero'],
             binaries=[],
             datas=[('*.ui','.')],
             hiddenimports=['PyQt5.sip',
                            'gevent.__hub_local',
                            'python36'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='manas',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
