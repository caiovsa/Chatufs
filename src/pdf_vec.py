import pymupdf4llm

md_text = pymupdf4llm.to_markdown("documents/PPC_-_Ci_ncia_da_Computa__o__1_.pdf")
with open("saida.md", "w", encoding="utf-8") as f:
    f.write(md_text)