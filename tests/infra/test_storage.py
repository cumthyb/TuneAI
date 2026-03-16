from tuneai.core.infra import storage


class TestStorage:
    def test_save_and_cleanup_request_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(storage, "get_outputs_dir", lambda: tmp_path)
        rid = "req_storage"
        input_data = b"input"
        output_data = b"output"

        in_path = storage.save_input_image(rid, input_data)
        out_path = storage.save_output_image(rid, output_data)

        assert in_path.exists()
        assert out_path.exists()
        assert storage.get_input_path(rid).read_bytes() == input_data
        assert storage.get_output_path(rid).read_bytes() == output_data

        storage.cleanup(rid)
        assert not (tmp_path / rid).exists()
