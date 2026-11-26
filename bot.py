import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime
import asyncio

# Configuração das Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Necessário para gerenciar/atribuir cargos aos membros

class MeuBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Registra as Views de forma persistente para funcionar mesmo após reiniciar
        self.add_view(TicketView())
        self.add_view(CloseTicketView())
        await self.tree.sync()
        print("Comandos Slash sincronizados com sucesso!")

bot = MeuBot()

# --- FORMULÁRIO (MODAL) DE FREE AGENT ---
class FreeAgentModal(discord.ui.Modal, title="Ficha de Free Agent"):
    
    posicao = discord.ui.TextInput(
        label="Sua Posição Principal",
        placeholder="Ex: Atacante, Goleiro, Meia-Atacante...",
        min_length=2,
        max_length=45,
        required=True
    )

    experiencia = discord.ui.TextInput(
        label="Sua Experiência / Histórico",
        placeholder="Ex: Joguei no Time X, campeão da Liga Y, 2 anos...",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=1000,
        required=True
    )

    adicional = discord.ui.TextInput(
        label="Observações / Plataforma",
        placeholder="Ex: Jogo no PC/PS5, procuro time competitivo...",
        style=discord.TextStyle.paragraph,
        min_length=2,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        ID_CANAL_FREE_AGENTS = 1574578965023170573
        
        canal_destino = interaction.guild.get_channel(ID_CANAL_FREE_AGENTS)

        if canal_destino:
            embed = discord.Embed(
                title="NOVO JOGADOR LIVRE (FREE AGENT)",
                color=discord.Color.from_rgb(128, 128, 128),
                description=f"O jogador {interaction.user.mention} está disponível para contratação!"
            )
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="Posição:", value=self.posicao.value, inline=False)
            embed.add_field(name="Experiência & Histórico:", value=self.experiencia.value, inline=False)
            
            if self.adicional.value:
                embed.add_field(name="Observações:", value=self.adicional.value, inline=False)
                
            embed.set_footer(text=f"ID do Jogador: {interaction.user.id}")

            await canal_destino.send(embed=embed)
            
            await interaction.response.send_message(
                f"Sua ficha de Free Agent foi publicada com sucesso no canal {canal_destino.mention}!", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "O canal de destino não foi encontrado! Verifique se o ID configurado no bot está correto.", 
                ephemeral=True
            )


# --- SISTEMA DE CONTRATO (BOTÕES DE ACEITAR E REJEITAR) ---
class ContractView(discord.ui.View):
    def __init__(self, signee: discord.Member, contractor: discord.Member, team: str, position: str, role: str, cargo_time: discord.Role):
        super().__init__(timeout=None)
        self.signee = signee
        self.contractor = contractor
        self.team = team
        self.position = position
        self.role = role
        self.cargo_time = cargo_time

    @discord.ui.button(label="ACCEPT", style=discord.ButtonStyle.success, custom_id="accept_contract")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.signee.id:
            await interaction.response.send_message("Apenas o jogador contratado pode aceitar esta proposta!", ephemeral=True)
            return

        # Atribui o cargo do time automaticamente ao aceitar
        try:
            await self.signee.add_roles(self.cargo_time, reason=f"Contrato aceito com o time {self.team}")
        except discord.Forbidden:
            print("ERRO: O bot não tem permissão para atribuir este cargo. Verifique se o cargo do bot está acima na hierarquia.")
        except Exception as e:
            print(f"Erro ao atribuir cargo: {e}")

        contract_id = f"{random.randint(100000000000000000, 999999999999999999)}"

        embed = discord.Embed(
            color=discord.Color.green(),
            description=f"✅ {self.signee.mention} accepted the contract!"
        )
        
        embed.set_author(name="CONTRACT ACCEPTED")
        embed.set_thumbnail(url=self.signee.display_avatar.url)
        
        embed.add_field(name="Signee", value=self.signee.mention, inline=False)
        embed.add_field(name="Contractor", value=self.contractor.mention, inline=False)
        embed.add_field(name="Contract ID", value=f"`{contract_id}`", inline=False)
        embed.add_field(name="Team", value=self.cargo_time.mention, inline=False)
        embed.add_field(name="Position", value=self.position, inline=False)
        embed.add_field(name="Role", value=self.role, inline=False)
        embed.add_field(name="Manager", value=self.contractor.mention, inline=False)

        self.clear_items()
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="REJECT", style=discord.ButtonStyle.danger, custom_id="reject_contract")
    async def reject(self, interaction: discord.Interaction):
        if interaction.user.id != self.signee.id:
            await interaction.response.send_message("Apenas o jogador contratado pode recusar esta proposta!", ephemeral=True)
            return

        embed = discord.Embed(
            color=discord.Color.red(),
            description=f"❌ {self.signee.mention} rejected the contract offer."
        )
        embed.set_author(name="CONTRACT REJECTED")

        self.clear_items()
        await interaction.response.edit_message(content=None, embed=embed, view=self)


# --- SISTEMA DE TICKET DE SUPORTE (PT / EN) ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fechar / Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_support_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔒 **O ticket será encerrado e deletado em 5 segundos...**\n"
            "*The ticket will be closed and deleted in 5 seconds...*"
        )
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Ticket de suporte encerrado")
        except Exception as e:
            print(f"Erro ao deletar canal de ticket: {e}")


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def criar_ticket(self, interaction: discord.Interaction, categoria: str, titulo: str, desc_pt: str, desc_en: str):
        guild = interaction.guild
        member = interaction.user

        nome_limpo = "".join(c for c in member.name.lower() if c.isalnum() or c == "-")
        nome_canal = f"{categoria}-{nome_limpo}"[:95]

        canal_existente = discord.utils.get(guild.text_channels, name=nome_canal)
        if canal_existente:
            await interaction.response.send_message(
                f"❌ Você já possui um ticket deste tipo aberto em {canal_existente.mention}!\n"
                f"*You already have an open ticket of this type in {canal_existente.mention}!*",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=nome_canal,
                overwrites=overwrites,
                topic=f"Ticket ({categoria}) de {member.name} (ID: {member.id})"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para criar canais! Verifique a permissão **Gerenciar Canais** do bot.\n"
                "*I don't have permission to create channels! Please check the bot's **Manage Channels** permission.*",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=titulo,
            color=discord.Color.blue(),
            description=(
                f"Olá {member.mention}!\n{desc_pt}\n\n"
                "---\n"
                f"*Hello {member.mention}!*\n*{desc_en}*"
            )
        )
        embed.set_footer(text="Clique abaixo para fechar | Click below to close")

        await ticket_channel.send(content=member.mention, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(
            f"✅ Seu ticket foi criado em {ticket_channel.mention}!\n"
            f"*Your ticket has been created in {ticket_channel.mention}!*",
            ephemeral=True
        )

    @discord.ui.button(label="👑 Ownar / Own a Club", style=discord.ButtonStyle.primary, custom_id="ticket_ownar_btn")
    async def btn_ownar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_ticket(
            interaction,
            categoria="ownar",
            titulo="OWNAR TIME / OWN A CLUB",
            desc_pt="Informe qual time você deseja assumir/gerenciar na liga e aguarde o retorno da administração.",
            desc_en="Please state which club/team you wish to manage in the league and wait for staff response."
        )

    @discord.ui.button(label="🤝 Partner / Parceria", style=discord.ButtonStyle.success, custom_id="ticket_partner_btn")
    async def btn_partner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_ticket(
            interaction,
            categoria="partner",
            titulo="PARCERIA / PARTNERSHIP",
            desc_pt="Envie os detalhes da sua proposta de parceria ou divulgação e aguarde nossa equipe.",
            desc_en="Send the details of your partnership or promotion proposal and wait for our team."
        )

    @discord.ui.button(label="❓ Ajuda / Help", style=discord.ButtonStyle.secondary, custom_id="ticket_ajuda_btn")
    async def btn_ajuda(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_ticket(
            interaction,
            categoria="ajuda",
            titulo="AJUDA & SUPORTE / HELP & SUPPORT",
            desc_pt="Descreva sua dúvida, problema ou denúncia com detalhes para que nossa equipe possa ajudar.",
            desc_en="Describe your question, issue, or report in detail so our staff can assist you."
        )

    @discord.ui.button(label="📌 Outros / Others", style=discord.ButtonStyle.secondary, custom_id="ticket_outros_btn")
    async def btn_outros(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_ticket(
            interaction,
            categoria="outros",
            titulo="OUTROS ASSUNTOS / OTHER SUBJECTS",
            desc_pt="Explique o motivo do seu contato e aguarde o atendimento da administração.",
            desc_en="Explain the reason for your contact and wait for staff assistance."
        )


# --- EVENTO ON READY ---
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

# --- COMANDO /SETUP-TICKET ---
@bot.tree.command(name="setup-ticket", description="Envia o painel de ticket de suporte em Português e Inglês.")
async def setup_ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Apenas administradores podem enviar o painel de tickets!\n"
            "*Only administrators can set up the ticket panel!*",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="CENTRAL DE ATENDIMENTO / SUPPORT CENTER",
        color=discord.Color.blue(),
        description=(
            "Selecione uma das opções abaixo para abrir um ticket privado:\n"
            "*Select one of the options below to open a private ticket:*\n\n"
            "👑 **Ownar / Own a Club** — Assumir um time / *Manage a club*\n"
            "🤝 **Partner / Parceria** — Propostas de parceria / *Partnership proposals*\n"
            "❓ **Ajuda / Help** — Dúvidas e suporte / *Questions and support*\n"
            "📌 **Outros / Others** — Demais assuntos / *Other subjects*"
        )
    )
    embed.set_footer(text="Suporte Oficial | Official Support")

    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message(
        "✅ Painel de ticket enviado com sucesso!\n"
        "*Ticket panel sent successfully!*",
        ephemeral=True
    )


# --- COMANDO /FREEAGENTS ---
@bot.tree.command(name="freeagents", description="Preencha a sua ficha para ficar disponível como Free Agent!")
async def freeagents(interaction: discord.Interaction):
    await interaction.response.send_modal(FreeAgentModal())


# --- COMANDO /OFFER ---
@bot.tree.command(name="offer", description="Envia uma proposta de contrato oficial para um jogador.")
@app_commands.describe(
    jogador="Marque o jogador que deseja contratar",
    cargo_time="Selecione o cargo do time que o jogador irá receber",
    time="Nome do time que está contratando",
    posicao="Posição em campo (ex: cm, st, gk)",
    role="Função no time (ex: titular, reserva)"
)
async def offer(
    interaction: discord.Interaction,
    jogador: discord.Member,
    cargo_time: discord.Role,
    time: str,
    posicao: str,
    role: str
):
    ID_CARGO_MANAGER = 1574578963567607938
    ID_CARGO_ASSISTANT_MANAGER = 1574578963567607937

    CARGOS_PERMITIDOS = [ID_CARGO_MANAGER, ID_CARGO_ASSISTANT_MANAGER]

    tem_cargo = any(role_obj.id in CARGOS_PERMITIDOS for role_obj in interaction.user.roles)

    if not tem_cargo:
        await interaction.response.send_message(
            "Você não tem permissão de cargo para utilizar este comando!", 
            ephemeral=True
        )
        return

    # ID do canal oficial onde as propostas devem ser publicadas
    ID_CANAL_CONTRACTS = 1574578965023170575
    canal_contratos = interaction.guild.get_channel(ID_CANAL_CONTRACTS)

    if not canal_contratos:
        await interaction.response.send_message(
            "❌ O canal de contratos configurado não foi encontrado!", 
            ephemeral=True
        )
        return

    embed = discord.Embed(
        color=discord.Color.blue()
    )
    embed.set_author(name="OFFERT CONTRACT")
    
    embed.add_field(name="Player", value=jogador.mention, inline=False)
    embed.add_field(name="Team", value=cargo_time.mention, inline=False)
    embed.add_field(name="Position", value=posicao, inline=False)
    embed.add_field(name="Role", value=role, inline=False)
    embed.add_field(name="Manager", value=interaction.user.mention, inline=False)

    view = ContractView(
        signee=jogador,
        contractor=interaction.user,
        team=time,
        position=posicao,
        role=role,
        cargo_time=cargo_time
    )

    # Envia a proposta no canal de contratos (destination)
    await canal_contratos.send(content=jogador.mention, embed=embed, view=view)

    # Confirma para o Manager no canal de bot-commands que a proposta foi enviada com sucesso (de forma privada/ephemeral)
    await interaction.response.send_message(
        f"✅ Proposta de contrato enviada com sucesso para o canal {canal_contratos.mention}!", 
        ephemeral=True
    )


# --- COMANDO /RELEASE ---
@bot.tree.command(name="release", description="Libera um jogador de seu time atual (Rescisão/Demissão).")
@app_commands.describe(
    jogador="Marque o jogador que deseja liberar",
    cargo_time="Selecione o cargo do time do jogador"
)
async def release(
    interaction: discord.Interaction,
    jogador: discord.Member,
    cargo_time: discord.Role
):
    ID_CARGO_MANAGER = 1574578963567607938

    # Permissão exclusiva para quem tem cargo de Manager (ou Admin)
    tem_cargo_manager = interaction.user.guild_permissions.administrator or any(role.id == ID_CARGO_MANAGER for role in interaction.user.roles)

    if not tem_cargo_manager:
        await interaction.response.send_message(
            "❌ Apenas membros com o cargo de Manager podem utilizar este comando!", 
            ephemeral=True
        )
        return

    # Verifica se o jogador realmente tem o cargo do time selecionado
    if cargo_time not in jogador.roles:
        await interaction.response.send_message(
            f"❌ O jogador {jogador.mention} não possui o cargo {cargo_time.mention} para ser liberado!", 
            ephemeral=True
        )
        return

    # Remove o cargo do time assim que o Manager confirma o comando
    try:
        await jogador.remove_roles(cargo_time, reason=f"Liberado por Manager {interaction.user.name}")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ O bot não tem permissão para remover este cargo. Mova o cargo do Bot para cima dos cargos dos times na lista de Cargos do Servidor!", 
            ephemeral=True
        )
        return
    except Exception as e:
        print(f"Erro ao remover cargo: {e}")

    # Envia o embed de confirmação de saída
    embed = discord.Embed(
        color=discord.Color.red(),
        description=f"🔴 {jogador.mention} He was released from {cargo_time.mention}!"
    )
    embed.set_author(name="CONTRACT REFUSED")
    embed.set_thumbnail(url=jogador.display_avatar.url)

    embed.add_field(name="Player", value=jogador.mention, inline=False)
    embed.add_field(name="Manager", value=interaction.user.mention, inline=False)
    embed.add_field(name="Team", value=cargo_time.mention, inline=False)
    
    embed.set_footer(text=f"Roster Cap • -1\nManager {interaction.user.name}")

    await interaction.response.send_message(embed=embed)


# --- FUNÇÃO AUXILIAR DE PERMISSÃO PARA OS COMANDOS /TWON E /TWOFF ---
def verificar_permissao_tw(interaction: discord.Interaction):
    ID_CARGO_FOUNDER = 1574578963601432580 
    ID_CARGO_DEVELOPER = 1574578963601432579

    cargos_permitidos = [ID_CARGO_FOUNDER, ID_CARGO_DEVELOPER]
    return interaction.user.guild_permissions.administrator or any(role_obj.id in cargos_permitidos for role_obj in interaction.user.roles)


# --- COMANDO /TWON (Abre / Destranca o canal em silêncio) ---
@bot.tree.command(name="twon", description="Destranca o canal atual.")
async def twon(interaction: discord.Interaction):
    if not verificar_permissao_tw(interaction):
        await interaction.response.send_message(
            "Você não tem permissão de cargo para utilizar este comando!", 
            ephemeral=True
        )
        return

    canal = interaction.channel
    await canal.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("Canal destrancado com sucesso!", ephemeral=True)


# --- COMANDO /TWOFF (Fecha / Tranca o canal em silêncio) ---
@bot.tree.command(name="twoff", description="Tranca o canal atual.")
async def twoff(interaction: discord.Interaction):
    if not verificar_permissao_tw(interaction):
        await interaction.response.send_message(
            "Você não tem permissão de cargo para utilizar este comando!", 
            ephemeral=True
        )
        return

    canal = interaction.channel
    await canal.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("Canal trancado com sucesso!", ephemeral=True)


bot.run("MTU3NTQ5MzE2MTU1ODQ4MzA4NQ.G3ZyAd.oiIQxoKn8izIcouSrZ3No4Pcr9Ld7CpCh5qPkQ")
