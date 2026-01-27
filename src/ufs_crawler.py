import asyncio
import os
import re
from playwright.async_api import async_playwright
from markdownify import markdownify as md

# Configurações
BASE_URL = "https://www.sigaa.ufs.br/sigaa/link/public/curso/curriculo/32672606"
OUTPUT_DIR = "/Users/caio/Caio_Things/Programacao/STI/chatbotUFS/documents"

async def save_content(title, content, url):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Limpa o título para ser um nome de arquivo válido
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip().replace(" ", "_")
    if not safe_title:
        safe_title = "documento_sem_titulo"
    
    # Adiciona prefixo para organizar
    filename = f"{safe_title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Source URL: {url}\n\n")
        f.write(content)
    print(f"💾 Salvo: {filepath}")

async def main():
    async with async_playwright() as p:
        print("🚀 Iniciando navegador...")
        # headless=False para visualização (opcional, mude para True se preferir não ver)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"🌍 Acessando {BASE_URL}...")
        await page.goto(BASE_URL)
        
        # Espera a tabela carregar
        try:
            await page.wait_for_selector('table', timeout=10000)
        except:
            print("⚠️ Tabela não encontrada ou timeout.")
        
        # Encontra os botões "Visualizar Programa"
        # O seletor busca links <a> com o título específico
        buttons_selector = 'a[title="Visualizar Programa"]'
        buttons = page.locator(buttons_selector)
        count = await buttons.count()
        print(f"🔎 Encontrados {count} botões de 'Visualizar Programa'.")
        
        for i in range(count):
            print(f"\n🔄 Processando item {i+1}/{count}...")
            
            # Verificação Robusta: Estamos na página de lista?
            # Se o botão não estiver visível ou se a URL mudou, recarregamos.
            # JSF muitas vezes mantêm a mesma URL mesmo navegando, então checar a URL não basta.
            is_list_visible = False
            try:
                # Tenta verificar se pelo menos o primeiro botão está visível
                if await page.locator(buttons_selector).first.is_visible(timeout=2000):
                    is_list_visible = True
            except:
                pass

            if not is_list_visible or page.url != BASE_URL:
                print("🔙 Voltando para a página principal (lista)...")
                await page.goto(BASE_URL)
                await page.wait_for_selector('table')
                # Dá um tempo extra para o JS do JSF bindar os eventos
                await asyncio.sleep(1)
            
            # Recarrega o locator SEMPRE, pois o DOM pode ter sido destruído/recriado
            buttons = page.locator(buttons_selector)
            
            # Pega o botão específico
            button = buttons.nth(i)
            
            # Verifica se o botão está visível
            if not await button.is_visible():
                print(f"⚠️ Botão {i+1} não visível, pulando.")
                continue

            # Tenta extrair o nome da disciplina da linha (tr)
            # Hierarquia: tr > td > a (botão)
            # Então subimos duas vezes (../..) para chegar ao tr
            # E pegamos o primeiro td
            discipline_name = f"Programa_Disciplina_{i+1}" # Fallback
            try:
                # Localiza a linha pai
                row = button.locator("xpath=../..")
                # Pega o texto da primeira coluna
                name_el = row.locator("td").first
                raw_name = await name_el.inner_text()
                if raw_name and raw_name.strip():
                    discipline_name = raw_name.strip()
                    print(f"   🔖 Disciplina identificada: {discipline_name}")
            except Exception as e:
                print(f"   ⚠️ Não foi possível ler o nome da disciplina: {e}")

            # Detecta se abre popup ou navega na mesma janela
            pages_before = len(context.pages)
            
            # Clica no botão
            try:
                await button.click()
            except Exception as e:
                print(f"❌ Erro ao clicar no botão {i+1}: {e}")
                continue
            
            # Espera um pouco para a ação ocorrer (popup abrir ou página navegar)
            await asyncio.sleep(2)
            
            pages_after = len(context.pages)
            is_popup = False
            
            if pages_after > pages_before:
                # Abriu uma nova janela/aba
                is_popup = True
                target_page = context.pages[-1]
                print("   📄 Detectado Popup/Nova Aba.")
            else:
                # Navegou na mesma janela (ou falhou, mas assumimos navegação)
                target_page = page
                print("   📄 Detectada navegação na mesma janela.")
            
            # Espera carregar o conteúdo da página alvo
            try:
                await target_page.wait_for_load_state("domcontentloaded")
                
                # Extrai dados
                target_url = target_page.url
                
                # Usa o nome da disciplina extraído anteriormente
                page_title = discipline_name
                
                print(f"   ⬇️ Extraindo conteúdo de: {page_title}")
                
                html_content = await target_page.content()
                markdown_text = md(html_content)
                
                await save_content(page_title, markdown_text, target_url)
                
            except Exception as e:
                print(f"❌ Erro ao extrair conteúdo da página: {e}")
            
            # Se for popup, fecha para limpar recurso
            if is_popup:
                await target_page.close()
            
            # Pausa de cortesia
            await asyncio.sleep(0.5)

        print("\n🏁 Processo finalizado!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
