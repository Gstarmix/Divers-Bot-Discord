import subprocess

bots = ['inscription_bot', 'mudae_help_bot', 'question_bot', 'presentation_bot']

processes = [subprocess.Popen(['python', f'{bot}/bot.py']) for bot in bots]

for process in processes:
    process.wait()