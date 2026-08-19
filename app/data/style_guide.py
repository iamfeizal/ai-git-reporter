"""
Style Guide & Few-Shot Examples for AI Narrative Generation.
Berisi contoh-contoh gaya bahasa dari referensi laporan (Golden Samples) 
untuk digunakan dalam In-Context Learning (ICL).
"""

FEW_SHOT_EXAMPLES = [
    {
        "context": "Perubahan UI pada kartu perpustakaan (menghilangkan logo YK, mengubah kategori anggota).",
        "output": "Pada periode ini dilakukan pembaruan desain kartu perpustakaan. Perubahan mencakup penghilangan logo YK yang sebelumnya ditampilkan pada kartu serta penyesuaian tampilan kategori dari yang sebelumnya adalah kategori jenis pekerjaan menjadi kategori jenis anggota perpustakaan agar lebih sesuai dengan tujuan kartu dan memberikan tampilan yang lebih mudah dikenali oleh pengguna dan petugas. Dibawah ini adalah tampilan sebelum dan sesudah dilakukannya perubahan pada tampilan kartu perpustakaan."
    },
    {
        "context": "Penambahan tombol navigasi back pada halaman Login dan Register.",
        "output": "Pada halaman login dan register ditambahkan tombol navigasi untuk kembali ke halaman sebelumnya. Perubahan ini bertujuan untuk memberikan fleksibilitas lebih bagi pengguna dalam berpindah halaman serta mengurangi kebingungan saat melakukan proses autentikasi. Dibawah ini adalah tampilan pada halaman login dan register sesudah dilakukannya penambahan navigasi."
    },
    {
        "context": "Perbaikan bug pada widget map yang tertutup tombol navigasi Android.",
        "output": "Ditemukan bug pada tampilan widget peta perpustakaan yang posisinya tertutup oleh navigasi Android sehingga menyulitkan pengguna untuk melihat tombol lokasi secara penuh. Perbaikan dilakukan dengan menambahkan komponen SafeArea(), sehingga seluruh elemen peta kini dapat ditampilkan dengan jelas tanpa terhalang oleh navigasi perangkat. Dibawah ini adalah tampilan form sesudah dilakukannya perbaikan bug pada halaman map perpustakaan."
    },
    {
        "context": "Perbaikan tombol form statis menjadi dinamis menyesuaikan konteks.",
        "output": "Perbaikan dilakukan pada tombol form disisi admin dalam layanan perpustakaan agar lebih dinamis. Sebelumnya, teks pada tombol bersifat statis dan tidak menyesuaikan konteks form yang sedang diakses. Dengan adanya perbaikan ini, teks tombol dapat berubah secara otomatis sesuai dengan kondisi form, sehingga meningkatkan kejelasan fungsi tombol bagi petugas maupun pengguna. Dibawah ini adalah tampilan tombol sebelum dan sesudah dilakukannya perubahan tombol pada form."
    }
]

def get_few_shot_prompt() -> str:
    """Format the few-shot examples into a prompt string."""
    prompt = "CONTOH GAYA BAHASA DAN PENULISAN (GOLDEN SAMPLES):\n\n"
    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        prompt += f"Kasus {i} (Konteks Teknis): {example['context']}\n"
        prompt += f"Output Narasi Bisnis: {example['output']}\n\n"
    return prompt
