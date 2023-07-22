import subprocess

bots = ['inscription_bot', 'mudae_help_bot', 'question_bot', 'presentation_bot']

processes = [subprocess.Popen(['python', 'bot.py', bot]) for bot in bots]

for process in processes:
    process.wait()
