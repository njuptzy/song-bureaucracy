# 当前数据库云端快照

快照日期：2026-08-04（Asia/Shanghai）。

本目录只跟踪当前使用的辞典库和结果库；`backups/`、`before-*`、`pre-*`、临时库和原书 PDF 不上传。所有列入文件在快照前均已通过 SQLite `integrity_check`。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `song_bureaucracy_dictionary.db` | 942080 | `1b18ddadd7432f82c6f8c08373a802c189ddeb4d57d596da2a8f15c0083f665f` |
| `song_bureaucracy_dictionary_ch1.db` | 544768 | `1eb0213594737d1b0856ef547824f289c448599ac19f1af331d7e90591a5ec4a` |
| `song_bureaucracy_dictionary_ch1t7.db` | 3592192 | `2a8bf0075500e83cfa74d0272eabd6d791c8b3301d5b944673061db2bbad3a7c` |
| `song_bureaucracy_dictionary_ch2t4.db` | 1495040 | `2ee9a4c31a9d37cadaa06bbf2d3e1f257326287c86d6f87d82017cd4441e3e49` |
| `song_bureaucracy_dictionary_ch5t7.db` | 1282048 | `7a0808fba531d192756de7c60b526171af7153efe39b34f4dc93770b28cc01b0` |
| `song_bureaucracy_dictionary_ch2t7.db` | 3055616 | `7ecc00473067d5afee85d4bb62eda56967a801444abf826450110fb396a78063` |
| `song_bureaucracy_dictionary_ch11t12.db` | 438272 | `f7f7f5526884067385c8ad3f806827a5e780260ea4fc23b0d14cec28741ee65d` |
| `song_bureaucracy_entries_ch1t7.db` | 35581952 | `819367b0a2c5884f7ce0428c628d43821485bb266d77a7e7509327029bc33d82` |
| `song_bureaucracy_entries_ch2t4.db` | 11116544 | `231dfebc2c6a18605fb118949e9f41651e17c4dab846152737e0fd826cb1acfb` |
| `song_bureaucracy_entries_ch5t7.db` | 28672 | `f89c8720d03589dc0d1ab64c942a1e6330b9e7ae73fc2f630d3aab797e8bf22a` |
| `song_bureaucracy_entries_ch2t7.db` | 35385344 | `4b4f9b2e3998118f6750ebe645ff095ace9d73b50557d9d63797f4f32388bec2` |
| `song_bureaucracy_entries_ch11t12.db` | 172032 | `740c55d92f7664f7f7f6ea8734708b5659e00e0c42355e332a298b927464fe53` |

另有三个显式跟踪的数据库快照：

- `agent-v0612/records/v0620-regen-test/song_bureaucracy_entries_v0620-regen-test.db`
- `vis/data/song_bureaucracy_best.db`（与上述 v0620 库完全同哈希）
- `vis/data/song_bureaucracy_visualization.db`

对应 SHA-256 分别为：

- `ba922e00bee78f669df622ccc265f0167251cf38977326b55b3f2621f8da4448`
- `ba922e00bee78f669df622ccc265f0167251cf38977326b55b3f2621f8da4448`
- `5625e3222fe3bbb8ee05641107f2ef9ce42e5cfd228a410cb85268078aa5f841`
