import json
import os
import shutil
import subprocess
from distutils.dir_util import copy_tree
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from sd_copy.dcim_transfer import Image, Video, get_dcim_transfers, get_image_or_video
from sd_copy.timelapse import patch_dcim_transfers_for_timelapse

DATA = "dcim"
FUJIFILM_DCIM = os.path.join(DATA, "100_Fuji")
DJI_OA_DCIM = os.path.join(DATA, "100MEDIA")
SD_COPY_TRANSFER_CMD = "poetry run sd-copy sort"


def _run_process(command: str):
    subprocess.run(command, check=True, shell=True)


def _folder_empty(path: str) -> bool:
    if os.path.exists(path) and os.path.isdir(path):
        return not os.listdir(path)
    else:
        raise Exception(f"Directory {path} does not exist")


def _number_of_files(dir_path: str) -> int:
    return len(tuple(path for path in Path(dir_path).rglob("*") if path.is_file()))


class TestSdCopySort(TestCase):
    def setUp(self):
        """Called for every test method. If this gets too much, use classmethod setUpClass instead."""

        if _folder_empty(path=DATA):
            raise Exception(f"Missing test data in {DATA}. Did you forget to update the submodule (see README)?")

        self.fuji_dcim_location = TemporaryDirectory()
        copy_tree(src=FUJIFILM_DCIM, dst=self.fuji_dcim_location.name)
        self.dji_oa_dcim_location = TemporaryDirectory()
        copy_tree(src=DJI_OA_DCIM, dst=self.dji_oa_dcim_location.name)

        self.output_location = TemporaryDirectory()

    def tearDown(self):
        # Make clean up explicit, even though it would be done without these commands
        self.fuji_dcim_location.cleanup()
        self.dji_oa_dcim_location.cleanup()
        self.output_location.cleanup()

    def test_running_sd_copy_sort_with_dry_run_does_not_copy_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"{SD_COPY_TRANSFER_CMD} {self.fuji_dcim_location.name} {self.output_location.name} --dry-run")
        self.assertTrue(_folder_empty(path=self.output_location.name))

    def test_running_sd_copy_sort_on_fujifilm_test_files_copies_expected_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"{SD_COPY_TRANSFER_CMD} {self.fuji_dcim_location.name} {self.output_location.name}")
        self.assertEqual(
            _number_of_files(self.output_location.name),
            _number_of_files(self.fuji_dcim_location.name),
        )

    def test_runnning_sd_copy_sort_on_dji_test_files_copies_expected_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"{SD_COPY_TRANSFER_CMD} {self.dji_oa_dcim_location.name} {self.output_location.name}")
        hidden_files = ("._DJI_0373.MOV",)
        self.assertEqual(
            _number_of_files(self.output_location.name),
            _number_of_files(self.dji_oa_dcim_location.name) - len(hidden_files),
        )

    def test_sd_copy_sort_handles_existing_output_locations_correctly(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        output_location_subfolder = os.path.join(self.output_location.name, "2021-09-14")
        os.mkdir(output_location_subfolder)
        self.assertTrue(_folder_empty(output_location_subfolder))
        _run_process(f"{SD_COPY_TRANSFER_CMD} {self.dji_oa_dcim_location.name} {self.output_location.name}")
        self.assertFalse(_folder_empty(output_location_subfolder))

    def test_timelapse_with_videos_raises_unexpected_data_error(self):
        self.assertRaises(
            subprocess.CalledProcessError,
            _run_process,
            f"{SD_COPY_TRANSFER_CMD} --timelapse {self.dji_oa_dcim_location.name} {self.output_location.name}",
        )

    def test_timelapse_raises_error_for_images_with_non_matching_intervals(self):
        timelapse_input_location = TemporaryDirectory()
        for img in ("DSCF0226.JPG", "DSCF0227.JPG", "DSCF0228.JPG"):
            shutil.copy2(Path(self.fuji_dcim_location.name) / img, Path(timelapse_input_location.name) / img)
        self.assertRaises(
            subprocess.CalledProcessError,
            _run_process,
            f"{SD_COPY_TRANSFER_CMD} --timelapse {timelapse_input_location.name} {self.output_location.name}",
        )


class TestGetImageOrVideo(TestCase):
    def test_fujifilm_get_image_or_video(self):
        fujifilm_dcim_path = Path(FUJIFILM_DCIM)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0226.JPG"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0226.JPG"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0231.RAF"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0229.MOV"), Video)

    def test_dji_oa_get_image_or_video(self):
        dji_oa_dcim_path = Path(DJI_OA_DCIM)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0373.MOV"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0375.MOV"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0375.AAC"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0376.JPG"), Image)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0377.MP4"), Video)


class TestGetDcimTransfers(TestCase):
    def setUp(self):
        self.input_output_map = json.loads(Path("tests/integration/expected_filenames.json").read_text())

    def _check_input_output_paths_of_dcim_transfers(self, dcim_dir: str, timelapse: bool):
        dcim_transfers = get_dcim_transfers(
            source_path=Path(f"dcim/{dcim_dir}"),
            destination_path=Path("/tmp"),
            time_offset=0,
        )
        if timelapse:
            dcim_transfers = patch_dcim_transfers_for_timelapse(dcim_transfers, dry_run=True)

        self.assertEqual(
            tuple(sorted(str(dcim_transfer.source_path) for dcim_transfer in dcim_transfers)),
            tuple(sorted(str(source_path) for source_path in self.input_output_map[dcim_dir].keys())),
        )

        for dcim_transfer in dcim_transfers:
            self.assertEqual(
                str(dcim_transfer.target_path),
                self.input_output_map[dcim_dir][str(dcim_transfer.source_path)],
            )

    def test_fuji_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100_Fuji", timelapse=False)

    def test_fuji_timelapse_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100_Fuji_timelapse", timelapse=True)

    def test_fuji_timelapse_raw_only_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100_Fuji_timelapse_raw_only", timelapse=True)

    def test_osmo_action_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100MEDIA", timelapse=False)

    def test_osmo_action_timelapse_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100MEDIA_timelapse", timelapse=True)

    def test_osmo_action_timed_photo_input_output_paths(self):
        self._check_input_output_paths_of_dcim_transfers(dcim_dir="100MEDIA_timed_photo", timelapse=True)
