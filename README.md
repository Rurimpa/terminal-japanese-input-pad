# terminal-japanese-input-pad（日本語入力パッド）

Windows Terminal の窓のすぐ下に、日本語を打つための入力窓を常設する小さな道具です。
A small always-on input box docked under Windows Terminal, for typing Japanese without the IME candidate window covering what you type.

個人が作った道具です。Anthropic・Microsoft・Google とは関係ありません。

## すぐ使う（3手）

1. **Python を入れる**（入っていれば飛ばす）：PowerShell かコマンドプロンプトで `winget install Python.Python.3.13`。または https://www.python.org/downloads/ から入れる
2. **ファイルを取る**：このページ上の緑の **Code** → **Download ZIP** で落とし、好きな場所に展開する
3. **`start_input_pad.bat` を2回クリック**する。Windows Terminal の窓の下に入力窓が出ます

あとは入力窓で日本語を打って **Enter** で送信。Windows Terminal で **Tab** を押すと入力窓へ飛びます。
終わるときは、入力窓の中で右クリック →「日本語入力パッドを終了する」。

ログインしたときに自動で立ち上げたいときは、`start_input_pad.bat` のショートカットを、スタートアップフォルダ（`Win+R` → `shell:startup`）に置いてください。

## なぜ作ったか

Windows Terminal で Claude Code などの対話型のコマンドラインツールを使うと、日本語入力（IME）の予測候補・変換候補の窓が、打っている文字の上に重なって読めないことがあります。
原因は Windows Terminal の不具合でした（[microsoft/terminal#20318](https://github.com/microsoft/terminal/issues/20318)）。参考：[anthropics/claude-code#70955](https://github.com/anthropics/claude-code/issues/70955)

**2026-10-02 に出た Windows Terminal 1.25.2733.0（Stable）と 1.24.12741.0 で直りました**（[microsoft/terminal#20627](https://github.com/microsoft/terminal/pull/20627)）。1.25.2733.0 で、窓を最大化したときもしていないときも、候補の窓が文字に重ならないことを確かめました（2026-10-29・Google 日本語入力）。重なって困っているなら、まず Windows Terminal を新しい版にしてください。

この道具は、もともと Windows Terminal の直しが届くまでのつなぎとして作りました。直ったあとも、長い文を書いて直してから送る・コピーや貼り付けがしやすい、などのために使い続けられます。

この道具は、Windows Terminal の窓のすぐ下に普通の Windows の入力窓を置きます。そこで打てば、候補の窓は文字の位置に正しく出て、重なりません。打ち終わって Enter を押すと、文が元の窓へ貼り付けられ、そのまま送信されます。

## できること

- Windows Terminal の窓の下に、同じ横幅でくっつく。窓を動かす・幅を変えるとついてくる。最小化すると一緒に隠れる
- 下に場所が無いときは、Windows Terminal の窓の高さを自動で縮める（最大化されていれば元に戻してから縮める）
- **Enter**＝貼り付けて送信／**Ctrl+Enter**＝貼り付けだけ／**Shift+Enter**＝改行／**Esc**＝元の窓へ戻る（書きかけは残る）
- **Ctrl+Shift+J**＝入力窓と元の窓を行き来する。入力窓をしまっているときは出し直す
- **Ctrl+C**（入力窓の中で、文字を選んでいないとき）＝元の窓へ Ctrl+C を送り、Claude Code・Codex の動きを止める（v0.7.0）。文字を選んでいるときはふつうのコピー
- Windows Terminal の窓ごとに入力窓が1つずつ出る（Claude Code と Codex を別の窓で開いているときなど・v0.8.0）。書きかけの文は入力窓ごとに別々に残り、窓を閉じるとその入力窓も消える
- **↑・↓・Enter**（入力窓が空のとき）＝元の窓へ送る（v0.10.0）。Claude Code の選ぶ画面（フォルダを信用するか・許可の質問・/model など）を、入力窓にいたまま選べる。文字があるときや日本語の変換中は、入力窓の中で働く
- **Win＋矢印**（入力窓が選ばれているとき）＝Windows Terminal の窓を寄せる（v0.9.1）。↑＝画面いっぱい／←→＝左半分・右半分／↓＝寄せる前の位置。左右半分から↑↓で上下4分の1。どれも下に入力窓の分を空ける。Windows のスナップ補助（残り半分に置く窓を選ぶ画面）は出ない
- **PrintScreen**（入力窓が選ばれているとき・ほかのキーと一緒に押していないとき）＝元の Windows Terminal の窓を選び直してから PrintScreen を渡し、撮り終わったら入力窓へ戻る（v0.12.0）。「アクティブな窓」を撮るスクリーンショットの道具（ShareX など）で、入力窓ではなく Windows Terminal の窓が撮れる。Shift+PrintScreen などは今までどおり。`config.json` に `"print_screen": false` と書くと切れる
- **Tab**（Windows Terminal が前にあるとき）＝入力窓へ飛ぶ（v0.5.0）。Ctrl・Shift・Alt・Win を押しているときと、入力窓をしまっているときは、ふつうの Tab として届く
- 入力窓を出しているときに Windows Terminal を選ぶ（クリック・Alt+Tab など）と、自動で入力窓へ移る（v0.6.0）。入力窓から **Esc** で戻ったときは移らないので、Claude Code の許可の質問に答えたり、Esc で止めたりできる。Tab などで入力窓へ戻ると、また移るようになる。窓のいちばん上の帯（タブ・∨・最小化など）を押したときは移らないので、∨ から設定などを開ける（v0.12.1）
- **「メモ：」で始まる文**＝元の窓へ送らず、`config.json` の `memo_file` に書いたファイルへ1行足す（v0.11.0・書いたときだけ動く）。下の「メモを受け取りファイルへ書く」を参照
- 上の線をつかんで上下に動かすと、入力窓の高さが変わる（覚えておく）
- **Ctrl+ホイール**または右クリックで、文字の大きさを変える（覚えておく）
- ファイルや画像を落とすと、その場所（フルパス）が入る（[tkinterdnd2](https://pypi.org/project/tkinterdnd2/) が入っているとき）
- 右クリック →「入力窓をしまう」でしまう
- 日本語入力で確定したハイフンやドットなどの半角の記号が tkinter で落ちる不具合を、確定文字列（`WM_IME_COMPOSITION` の `GCS_RESULTSTR`）を直接受け取ることで避けている

## 動く環境

- Windows 10 / 11
- Windows Terminal
- Python 3.10 以降（3.13 で確認）。tkinter は Python に同梱
- 任意：`pip install tkinterdnd2`（ファイルを落とす機能を使うとき）
- 日本語入力は Google 日本語入力で確かめています。Microsoft IME・ATOK では確かめていません

## 使い方（コマンドで起動するとき）

```
pythonw input_pad.pyw
```

二重起動はしません（2つ目は何もせずに終わります）。

## 設定（任意）

`input_pad.pyw` と同じフォルダに `config.json` を置くと、既定値を変えられます。文字の大きさと入力窓の高さは、操作すると自動でここに書かれます。

```json
{
  "hotkey_modifiers": ["ctrl", "shift"],
  "hotkey_key": "J",
  "font_family": "BIZ UDゴシック",
  "font_size": 14,
  "pad_lines": 3,
  "tab_jump": true,
  "auto_focus": true,
  "pad_height": 120,
  "memo_file": "",
  "print_screen": true
}
```

### メモを受け取りファイルへ書く（任意・v0.11.0）

`memo_file` にファイルの場所を書くと、「メモ：」「メモ:」「メモ；」「メモ;」「めも：」で始まる文を Enter（または Ctrl+Enter）で送ったとき、元の窓へは貼り付けず、そのファイルへ1行足して入力窓を空にします。空（既定）のときは、今までどおり元の窓へ送ります。

```json
{
  "memo_file": "C:\\Users\\you\\memos.jsonl"
}
```

足す1行の形（JSON Lines）：

```json
{"at":"2026-10-10 13:25:51","seat_dir":"","session_id":"","text":"メモの本文","source":"input_pad","window":"送り先の窓の題名"}
```

`seat_dir` と `session_id` は、Claude Code のフックで同じファイルへ書く仕組みと並べて使うための欄で、入力窓からは分からないので空です。書けなかったときは、文を欄に残し、下の案内の行に赤字で知らせます。

## 記録（ログ）

`logs\input_pad_YYYYMMDD.log` に動きの記録を残します。打った文の中身は残さず、文字数だけを残します。ただし、送り先の窓の題名（Windows Terminal のタブの名前）は記録に残ります。また、自動で入力窓へ移る働きのために、切り替えた窓の種類名（例 `Chrome_WidgetWin_1`。窓の題名ではありません）も記録に残ります。自動で入力窓へ移した・移さなかったときは、そのときのマウスの位置（Windows Terminal の窓の左上からの位置）も残ります（v0.12.1）。

## 既知の制限

- 送るときにクリップボードを使います（送った文がクリップボードに残ります）
- 送る先は、Windows Terminal の窓でいま開いているタブです
- スクリーンショット道具で「アクティブな窓」を PrintScreen 以外のキーで撮る設定にしているときは、入力窓を選んでいると入力窓だけが撮れます（別の窓のため）。PrintScreen で撮るときは、v0.12.0 から Windows Terminal の窓が撮れます（その写真に入力窓は入りません）
- Tab で入力窓へ飛ぶため、Windows Terminal の中では Tab で候補を確定する操作（Claude Code の / のコマンドやファイル名の候補など）が使えません。使いたいときは `config.json` に `"tab_jump": false` と書いてください。Windows Terminal に直接日本語を打っていて、変換中に Tab で予測候補を選ぶ操作も入力窓へ飛ぶ動きになります
- 2行以上の文を送ると、Windows Terminal が「複数行を貼り付けますか」という警告を出し、入力窓の Enter がその警告の「貼り付け」に使われることがあります（コマンドプロンプトなどで最後の行が実行されずに残ります）。Windows Terminal の設定（settings.json）に "warning.multiLinePaste": false を足すと、警告が出なくなります

## ライセンス

MIT License（`LICENSE` を参照）。自由に使い、直し、組み込んでかまいません。そのときは、作者名（Rurimpa）とこの置き場のアドレスを残してください。MIT ライセンスそのものが、`LICENSE` に書かれた作者の表示を、写したものすべてに残すことを求めています。

作者：Rurimpa（https://github.com/Rurimpa）
