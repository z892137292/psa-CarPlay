#!/usr/bin/env python3
"""Exercise production guards against deliberate regressions, not a parallel policy model."""
import pathlib, shutil, subprocess, sys, tempfile, unittest
SOURCE = pathlib.Path(sys.argv.pop())
class PsaSourceRegressionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        for name in ('shared', 'common', 'mobile'):
            shutil.copytree(SOURCE/name, self.root/name, ignore=shutil.ignore_patterns('build', '.cxx', '.gradle'))
    def tearDown(self): self.temp.cleanup()
    def guard(self, script):
        return subprocess.run([sys.executable, str(pathlib.Path(__file__).parent/script), str(self.root)], capture_output=True, text=True)
    def test_removed_audio_getter_cannot_reappear_under_another_variable_name(self):
        path=self.root/'shared/src/main/java/com/shilapi/xcertplay/media/AndroidMediaSink.kt'
        path.write_text(path.read_text()+'\nfun invalid(vendorTrack: android.media.AudioTrack) = vendorTrack.audioAttributes\n')
        result=self.guard('verify_psa_rom.py')
        self.assertNotEqual(0, result.returncode); self.assertIn('ROM-incompatible', result.stderr)
    def test_deleted_p2p_controller_is_rejected(self):
        path=self.root/'shared/src/main/java/InvalidExperiment.kt'
        path.write_text('val manager: android.net.wifi.p2p.WifiP2pManager? = null')
        result=self.guard('verify_formal_tree.py')
        self.assertNotEqual(0, result.returncode); self.assertIn('Forbidden experiment', result.stderr)
    def test_deleted_softap_creation_is_rejected(self):
        path=self.root/'shared/src/main/java/InvalidExperiment.kt'
        path.write_text('fun invalid() { wifi.startLocalOnlyHotspot() }')
        result=self.guard('verify_formal_tree.py')
        self.assertNotEqual(0, result.returncode); self.assertIn('Forbidden experiment', result.stderr)
unittest.main()
