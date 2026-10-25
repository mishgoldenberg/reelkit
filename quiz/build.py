# python quiz/build.py git  ->  quiz/git.timing.js (timeline for quiz.html) + quiz/git.raw.wav (sound effects only)
# Rapid-fire quiz reel: 4 questions, 4 floating answer boxes, a 3-second ticking timer, then the right box turns green with a check.
# One timeline drives picture and sound. Every fact below is standard tool behaviour; the "why" line says it in one sentence.
import json, os, subprocess, sys, wave, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
SR = 48000
rng = np.random.default_rng(11)

# ok = index of the right option (0-3). Options are written in display order, so vary ok by hand.
QUIZZES = {
    'git': {
        'topic': 'Git', 'intro': '4 Git\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Which one throws away your uncommitted changes?', 'code': True,
             'opts': ['git stash', 'git fetch', 'git reset --hard', 'git commit --amend'], 'ok': 2,
             'why': 'reset --hard overwrites tracked files. There is no undo.'},
            {'q': 'Wrong branch. Undo the last commit but keep the changes:', 'code': True,
             'opts': ['git reset --soft HEAD~1', 'git revert HEAD', 'git checkout -- .', 'git push --force'], 'ok': 0,
             'why': '--soft moves the branch back. Your changes stay staged.'},
            {'q': 'Which one downloads and never touches your files?', 'code': True,
             'opts': ['git pull', 'git merge', 'git rebase', 'git fetch'], 'ok': 3,
             'why': 'fetch only updates remote branches. pull = fetch + merge.'},
            {'q': 'Which one is safe on a branch your team shares?', 'code': True,
             'opts': ['git commit --amend', 'git revert <sha>', 'git rebase -i', 'git push --force'], 'ok': 1,
             'why': 'revert adds a new commit that undoes the old one. History stays.'},
        ],
    },
    'docker': {
        'topic': 'Docker', 'intro': '4 Docker\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Which one bakes your secret into the image?', 'code': True,
             'opts': ['RUN --mount=type=secret,id=tk', 'docker run -e TOKEN=…', 'COPY .env /app/.env', '.env in .dockerignore'], 'ok': 2,
             'why': 'Even if a later RUN deletes it, the file stays in an earlier layer.'},
            {'q': 'Container dies with exit code 137. Most likely?', 'code': False,
             'opts': ['A syntax error', 'Port already in use', 'Image not found', 'Killed: out of memory'], 'ok': 3,
             'why': '137 = 128 + 9 (SIGKILL). Usually the OOM killer.'},
            {'q': 'docker system prune. What does it keep by default?', 'code': False,
             'opts': ['Volumes', 'Stopped containers', 'Dangling images', 'Unused networks'], 'ok': 0,
             'why': 'Volumes are only pruned with --volumes.'},
            {'q': 'Which base image is the smallest?', 'code': True,
             'opts': ['ubuntu:24.04', 'alpine:3.20', 'debian:bookworm', 'node:22'], 'ok': 1,
             'why': 'Alpine is under 10 MB. node:22 is over 1 GB.'},
        ],
    },
    'k8s': {
        'topic': 'Kubernetes', 'intro': '4 Kubernetes\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'CrashLoopBackOff. What is actually happening?', 'code': False,
             'opts': ['The image cannot be pulled', 'The container keeps starting and exiting', 'The node is out of disk', 'The pod waits for a node'], 'ok': 1,
             'why': 'Kubernetes keeps restarting it, waiting longer each time.'},
            {'q': 'A pod is stuck in Pending. Which command tells you why?', 'code': True,
             'opts': ['kubectl logs <pod>', 'kubectl exec <pod>', 'kubectl describe pod <pod>', 'kubectl top pod'], 'ok': 2,
             'why': 'The Events say what the scheduler could not do. Pending pods have no logs.'},
            {'q': 'Your Service has no endpoints. Most likely?', 'code': False,
             'opts': ['Selector does not match pod labels', 'Too many replicas', 'NodePort already taken', 'Ingress is missing'], 'ok': 0,
             'why': 'No pod matches the selector, so there is nothing to send traffic to.'},
            {'q': 'ImagePullBackOff. What do you check first?', 'code': False,
             'opts': ['CPU limits', 'The liveness probe', 'The Service selector', 'Image name, tag and registry access'], 'ok': 3,
             'why': 'A typo in the tag or a missing pull secret causes most of these.'},
        ],
    },
    'linux': {
        'topic': 'Linux', 'intro': '4 Linux\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Which cron line runs every 5 minutes?', 'code': True,
             'opts': ['5 * * * *', '* */5 * * *', '*/5 * * * *', '0 5 * * *'], 'ok': 2,
             'why': '5 * * * * runs once an hour, at minute 5.'},
            {'q': 'chmod 755 script.sh. What do other users get?', 'code': False,
             'opts': ['Read and execute', 'Read and write', 'Execute only', 'Nothing'], 'ok': 0,
             'why': '7 = rwx for you, 5 = r-x for group and others.'},
            {'q': 'Disk is 100% full, but du finds nothing big. Why?', 'code': False,
             'opts': ['RAM is full', 'Too many users logged in', 'A deleted file is still held open', 'DNS is down'], 'ok': 2,
             'why': 'lsof +L1 shows it. Restart the process to free the space.'},
            {'q': 'Which one shows what is listening on port 8080?', 'code': True,
             'opts': ['ps aux', 'df -h', 'top', 'ss -ltnp'], 'ok': 3,
             'why': '-l listening, -t TCP, -n numeric ports, -p the process.'},
        ],
    },
    'terraform': {
        'topic': 'Terraform', 'intro': '4 Terraform\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'In a plan, which symbol means destroy, then create again?', 'code': True,
             'opts': ['+', '~', '-/+', '<='], 'ok': 2,
             'why': '~ updates in place. -/+ replaces the resource.'},
            {'q': 'You renamed a resource. The plan wants to destroy it. Fix?', 'code': False,
             'opts': ['Add a moved block', 'terraform taint', 'Delete the state file', 'Run with -target'], 'ok': 0,
             'why': 'moved tells Terraform it is the same object under a new name.'},
            {'q': 'Two people run apply at the same time. What stops it?', 'code': False,
             'opts': ['.terraform.lock.hcl', 'Workspaces', 'State locking', '-parallelism=1'], 'ok': 2,
             'why': '.terraform.lock.hcl pins provider versions. It does not lock state.'},
            {'q': 'Which one makes terraform destroy fail on your database?', 'code': True,
             'opts': ['ignore_changes', 'prevent_destroy = true', 'depends_on', 'count = 0'], 'ok': 1,
             'why': 'Any plan that would destroy it errors out instead.'},
        ],
    },
    'aws': {
        'topic': 'AWS', 'intro': '4 AWS\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Cheapest S3 storage class for data you almost never read?', 'code': False,
             'opts': ['S3 Standard', 'S3 Glacier Deep Archive', 'S3 Intelligent-Tiering', 'S3 One Zone-IA'], 'ok': 1,
             'why': 'Lowest price per GB. Getting the data back takes hours.'},
            {'q': 'Your EC2 instance has no public IP. How does it reach the internet?', 'code': False,
             'opts': ['An internet gateway alone', 'VPC peering', 'An Elastic IP on the subnet', 'A NAT gateway'], 'ok': 3,
             'why': 'A NAT gateway in a public subnet sends the traffic out for it.'},
            {'q': 'How should your app on EC2 get its AWS access?', 'code': False,
             'opts': ['An IAM role', 'Access keys in .env', 'The root account keys', 'Keys baked into the AMI'], 'ok': 0,
             'why': 'A role hands out short-lived credentials. Nothing to leak.'},
            {'q': 'What is the longest a Lambda function can run?', 'code': False,
             'opts': ['5 minutes', '1 hour', '15 minutes', 'No limit'], 'ok': 2,
             'why': '15 minutes, then it is stopped. Longer jobs belong elsewhere.'},
        ],
    },
    'claude': {
        'topic': 'Claude Code', 'intro': '4 Claude\nCode questions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Where does Claude Code read your project rules every session?', 'code': True,
             'opts': ['README.md', 'CLAUDE.md', '.clauderc', 'package.json'], 'ok': 1,
             'why': 'CLAUDE.md is loaded as context at the start of each session.'},
            {'q': 'Which one runs every time, no matter what Claude decides?', 'code': False,
             'opts': ['A line in CLAUDE.md', 'A skill', 'A hook', 'A subagent'], 'ok': 2,
             'why': 'Hooks are shell commands that run at fixed points in the lifecycle.'},
            {'q': 'Context is almost full. Which command summarizes the chat to free space?', 'code': True,
             'opts': ['/clear', '/compact', '/init', '/cost'], 'ok': 1,
             'why': '/clear wipes the conversation. /compact keeps a summary.'},
            {'q': 'Which one gives a side task its own context window?', 'code': False,
             'opts': ['A subagent', 'A slash command', 'A hook', 'An MCP server'], 'ok': 0,
             'why': 'A subagent works in its own context, so yours stays clean.'},
        ],
    },
    'sql': {
        'topic': 'SQL', 'intro': '4 SQL\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Which one deletes the table itself?', 'code': True,
             'opts': ['DELETE FROM users', 'TRUNCATE users', 'DROP TABLE users', 'UPDATE users SET …'], 'ok': 2,
             'why': 'DELETE and TRUNCATE empty the table. DROP removes it.'},
            {'q': "UPDATE users SET plan = 'pro' with no WHERE. What changes?", 'code': False,
             'opts': ['Nothing', 'Every row', 'Only the first row', 'It errors out'], 'ok': 1,
             'why': 'No WHERE means every row. Run the SELECT first.'},
            {'q': 'Which JOIN keeps left-table rows that have no match?', 'code': True,
             'opts': ['INNER JOIN', 'CROSS JOIN', 'SELF JOIN', 'LEFT JOIN'], 'ok': 3,
             'why': 'INNER drops them. LEFT keeps them, with NULLs.'},
            {'q': 'Which one makes a lookup by email fast?', 'code': False,
             'opts': ['An index on email', 'A bigger server', 'SELECT DISTINCT', 'A view'], 'ok': 0,
             'why': 'Without an index the database reads every row.'},
        ],
    },
    'cicd': {
        'topic': 'GitHub Actions', 'intro': '4 GitHub\nActions\nquestions.\n<hl>3 seconds each.</hl>',
        'qs': [
            {'q': 'Where do GitHub Actions workflow files live?', 'code': True,
             'opts': ['.github/workflows/', '.ci/', 'actions/', '.git/hooks/'], 'ok': 0,
             'why': 'Any .yml file in .github/workflows/ is a workflow.'},
            {'q': 'Where should a deploy token go?', 'code': False,
             'opts': ['In the workflow YAML', 'In a repository secret', 'In the README', 'In a commit message'], 'ok': 1,
             'why': 'Secrets are encrypted and masked in the logs.'},
            {'q': 'Which trigger runs a workflow on every pull request?', 'code': True,
             'opts': ['on: push', 'on: schedule', 'on: pull_request', 'on: release'], 'ok': 2,
             'why': 'push runs on commits. schedule runs on a cron.'},
            {'q': 'A job has to wait for another job. Which key?', 'code': True,
             'opts': ['depends_on', 'after', 'requires', 'needs'], 'ok': 3,
             'why': 'needs: build makes the job wait for build to finish.'},
        ],
    },
    'linux2': {
        'topic': 'Linux', 'intro': '4 more Linux\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Show the last 50 lines of a log and keep following it:', 'code': True,
             'opts': ['head -50 app.log', 'cat -n 50 app.log', 'tail -n 50 -f app.log', 'less +50 app.log'], 'ok': 2,
             'why': '-n 50 starts at the last 50 lines, -f keeps printing new ones.'},
            {'q': 'Which signal can a process NOT catch or ignore?', 'code': True,
             'opts': ['SIGTERM', 'SIGKILL', 'SIGINT', 'SIGHUP'], 'ok': 1,
             'why': 'kill -9 sends SIGKILL. The process gets no say.'},
            {'q': 'Where do system config files live by convention?', 'code': True,
             'opts': ['/var', '/usr/bin', '/tmp', '/etc'], 'ok': 3,
             'why': '/etc holds config. /var holds data that changes, like logs.'},
            {'q': 'What does 2>&1 do at the end of a command?', 'code': False,
             'opts': ['Sends errors where normal output goes', 'Runs the command twice', 'Hides all output', 'Writes output to a file named 1'], 'ok': 0,
             'why': '2 is stderr, 1 is stdout. 2>&1 points errors at stdout.'},
        ],
    },
    'bash': {
        'topic': 'Bash', 'intro': '4 Bash\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Which test is true only if the file exists?', 'code': True,
             'opts': ['[ -z file ]', '[ -f file ]', '[ -n file ]', '[ -s "" ]'], 'ok': 1,
             'why': '-f: exists and is a regular file. -z and -n test strings.'},
            {'q': 'What does set -e do in a script?', 'code': False,
             'opts': ['Echoes every command', 'Exports all variables', 'Stops at the first failing command', 'Turns on extended globs'], 'ok': 2,
             'why': 'set -x echoes commands. set -e exits on the first error.'},
            {'q': 'Which one prints the exit code of the last command?', 'code': True,
             'opts': ['echo $!', 'echo $$', 'echo $#', 'echo $?'], 'ok': 3,
             'why': '$! is the last background PID, $$ this shell, $# the arg count.'},
            {'q': 'Which quotes keep $HOME from expanding?', 'code': True,
             'opts': ["'single quotes'", '"double quotes"', '`backticks`', 'no quotes'], 'ok': 0,
             'why': 'Single quotes keep everything literal. Double quotes still expand.'},
        ],
    },
    # new Git questions (the first Git quiz was already posted), for the watermelon hook
    'git2': {
        'topic': 'Git', 'intro': '4 more Git\nquestions.\n<hl>3 seconds</hl>\n<hl>each.</hl>',
        'qs': [
            {'q': 'Put your unfinished changes aside so you can switch branches:', 'code': True,
             'opts': ['git stash', 'git save', 'git shelve', 'git park'], 'ok': 0,
             'why': 'git stash saves them; git stash pop brings them back.'},
            {'q': 'Which one shows who last changed each line of a file?', 'code': True,
             'opts': ['git log -p', 'git show', 'git blame', 'git who'], 'ok': 2,
             'why': 'git blame prints the commit and author of every line.'},
            {'q': 'Typo in your last commit message. Fix it:', 'code': True,
             'opts': ['git reset --msg', 'git commit --amend', 'git rebase --fix', 'git message'], 'ok': 1,
             'why': '--amend rewrites the last commit. Only before you push it.'},
            {'q': 'Which one lists branches already merged into this one?', 'code': True,
             'opts': ['git branch -m', 'git merge --list', 'git log --merged', 'git branch --merged'], 'ok': 3,
             'why': 'Safe to delete those. git branch -m renames a branch.'},
        ],
    },
}

# What the voice says (TTS-friendly spellings). Index 0 = intro card, 1-4 = questions, 5 = score card.
SAY = {
    'k8s': ['Kubernetes', ['Crash loop back off. What is actually happening?', 'A pod is stuck in Pending. Which command tells you why?',
                           'Your Service has no endpoints. What is most likely wrong?', 'Image pull back off. What do you check first?']],
    'linux': ['Linux', ['Which cron line runs every five minutes?', 'chmod seven five five. What do other users get?',
                        'The disk is full, but D U finds nothing big. Why?', 'Which one shows what is listening on port eighty eighty?']],
    'terraform': ['Terraform', ['In a plan, which symbol means destroy, then create again?', 'You renamed a resource, and the plan wants to destroy it. How do you fix it?',
                                'Two people run apply at the same time. What stops it?', 'Which one makes terraform destroy fail on your database?']],
    'aws': ['A W S', ['Which S three storage class is cheapest for data you almost never read?', 'Your E C two instance has no public I P. How does it reach the internet?',
                      'How should your app on E C two get its A W S access?', 'What is the longest a Lambda function can run?']],
    'claude': ['Claude Code', ['Where does Claude Code read your project rules every session?', 'Which one runs every time, no matter what Claude decides?',
                               'Your context is almost full. Which command summarizes the chat to free up space?', 'Which one gives a side task its own context window?']],
    'sql': ['S Q L', ['Which one deletes the table itself?', 'An update with no where clause. What changes?',
                      'Which join keeps rows from the left table that have no match?', 'Which one makes a lookup by email fast?']],
    'linux2': ['more Linux', ['Show the last fifty lines of a log, and keep following it.', 'Which signal can a process not catch or ignore?',
                              'Where do system config files live?', 'What does two, greater than, ampersand, one do at the end of a command?'],
               'Four questions. Three seconds each.'],      # after the shark hook card ("Scared? ... Try to answer all of them."), so no "But first"
    'bash': ['Bash', ['Which test is true only if the file exists?', 'What does set minus e do in a script?',
                      'Which one prints the exit code of the last command?', 'Which quotes keep dollar home from expanding?'],
             'Four questions. Three seconds each.'],        # after the robot-fall hook card
    'git2': ['Git', ['Put your unfinished changes aside, so you can switch branches.', 'Which one shows who last changed each line of a file?',
                     'Typo in your last commit message. Fix it.', 'Which one lists the branches already merged into this one?'],
             'But first: four more questions about Git. Three seconds each.'],
    'git': ['Git', ['Which one throws away your uncommitted changes?', 'Wrong branch. Undo the last commit, but keep the changes.',
                    'Which one downloads, and never touches your files?', 'Which one is safe on a branch your team shares?'],
            'But first: four questions about Git. Three seconds each.'],   # Kokoro's "four Git questions" sounds like "get"
    'cicd': ['GitHub Actions', ['Where do GitHub Actions workflow files live?', 'Where should a deploy token go?',
                                'Which trigger runs a workflow on every pull request?', 'A job has to wait for another job. Which key do you use?']],
}

def lines(name):
    topic, qs, *intro = SAY[name]                  # optional third item replaces the spoken intro
    return [intro[0] if intro else f'But first: four {topic} questions. Three seconds each.', *qs, 'How many did you get? Comment your score.']

INTRO, QLEN, OUTRO = 1.9, 6.4, 2.8
BOX_AT = [.35, .5, .65, .8]           # each box pops in
TIMER = (1.0, 4.0)                    # 3-second countdown, reveal at 4.0
WHY_AT = 4.45

def timeline(Z, vd=None):
    # vd = voice durations [intro, q1..q4, score]; with a voice the 3-second timer starts once the question has been read
    r = lambda x: round(x, 3)
    vd = vd or [0] * (len(Z['qs']) + 2)
    intro = max(INTRO, vd[0] + .55)
    T = {'intro': [0.0, r(intro)], 'qs': []}
    t = intro
    for k, _ in enumerate(Z['qs']):
        ta = max(TIMER[0], vd[1 + k] + .35)
        tb = ta + (TIMER[1] - TIMER[0])
        L = tb + (QLEN - TIMER[1])
        T['qs'].append({'t0': r(t), 't1': r(t + L), 'timer': [r(ta), r(tb)], 'why': r(tb + WHY_AT - TIMER[1]), 'box': BOX_AT})
        t += L
    outro = max(OUTRO, vd[-1] + .9)
    T['outro'] = [r(t), r(t + outro)]
    T['end'] = r(t + outro)
    T['box'], T['timer'], T['why'] = BOX_AT, TIMER, WHY_AT
    return T

def voice(name):                      # quiz/vo/<name>/<i>.wav, 48 kHz mono, made by quiz/voice.sh
    d = HERE / 'vo' / name
    if not (d / '0.wav').exists(): return None
    out = []
    for i in range(6):
        with wave.open(str(d / f'{i}.wav')) as w:
            out.append(np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768)
    return out

# ---- sound design (all synthesized, nothing downloaded) ----
def env(n, a, d):
    x = np.arange(n) / SR
    return np.minimum(1, x / max(a, 1e-4)) * np.exp(-x / d)

def bandnoise(n, lo, hi):
    s = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    s[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(s, n); return y / (np.abs(y).max() + 1e-9)

def tone(f, dur, a, d, g):
    n = int(dur * SR); return np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, a, d) * g

def tick(hi=True):                    # clock tick / tock
    n = int(.08 * SR)
    return (tone(2600 if hi else 1900, .08, .0005, .012, .5) + bandnoise(n, 2000, 8000) * env(n, .0003, .004) * .35)

def pop(k):
    n = int(.18 * SR); x = np.arange(n) / SR
    f = (520 + 90 * k) * np.exp(-x * 9) + 260
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .05) * .55

def whoosh(dur=.4):
    n = int(dur * SR); x = np.linspace(0, 1, n)
    return bandnoise(n, 300, 6000) * np.sin(np.pi * x) ** 2 * .3

def hit():
    n = int(1.0 * SR); x = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 55 * x) + .5 * np.sin(2 * np.pi * 110 * x)) * env(n, .003, .3)
    return y * .85 + bandnoise(n, 200, 4000) * env(n, .0008, .03) * .4

def ding():                           # right answer: bright two-note chime
    g = int(.12 * SR)
    return np.pad(tone(1047, .6, .002, .18, .5), (0, g)) + np.pad(tone(1568, .6, .002, .25, .55), (g, 0))

def bed(vo, n):                       # quiet CC0 lo-fi loop (sfx/cc0/CREDITS.txt), dips under the voice
    raw = subprocess.run([os.environ.get('FFMPEG', 'ffmpeg'), '-v', 'error', '-i', str(HERE.parent / 'sfx' / 'cc0' / 'music.mp3'),
                          '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    m = np.frombuffer(raw, dtype='<i2').astype(float) / 32768; m = np.tile(m, n // len(m) + 1)[:n]; m /= np.abs(m).max() + 1e-9
    e = np.convolve(np.abs(vo), np.ones(SR // 5) / (SR // 5), 'same'); talk = np.clip(e / (e.max() + 1e-9) * 6, 0, 1)
    g = (.11 - .05 * talk) * np.clip(np.arange(n) / (.6 * SR), 0, 1) * np.clip((n - np.arange(n)) / (1.4 * SR), 0, 1)
    return m * g

def build(name):
    Z = QUIZZES[name]; V = voice(name)
    T = timeline(Z, [len(v) / SR for v in V] if V else None)
    out = np.zeros(int((T['end'] + .5) * SR)); vo = np.zeros_like(out)
    def put(sig, t, buf=out):
        i = int(t * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]
    put(hit() * .6, 0.0)
    for q in T['qs']:
        t0, (ta, tb) = q['t0'], q['timer']
        put(whoosh(.35), t0 - .22); put(hit() * .35, t0)
        for k, b in enumerate(BOX_AT): put(pop(k), t0 + b)
        for k in range(6): put(tick(k % 2 == 0) * (1.0 if k % 2 == 0 else .55), t0 + ta + .5 * k)
        put(ding(), t0 + tb)
    put(whoosh(.35), T['outro'][0] - .22); put(hit(), T['outro'][0])
    out = out / (np.abs(out).max() + 1e-9)
    if V:                                 # voice on top, effects tucked under it
        put(V[0], .15, vo)
        for k, q in enumerate(T['qs']): put(V[1 + k], q['t0'] + .2, vo)
        put(V[-1], T['outro'][0] + .25, vo)
        vo = vo / (np.abs(vo).max() + 1e-9) * .95
        out = out * .42 + vo + bed(vo, len(out))
    out = out / (np.abs(out).max() + 1e-9) * .89
    pcm = (np.repeat(out[:, None], 2, axis=1) * 32767).astype('<i2')
    with wave.open(str(HERE / f'{name}.raw.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    hop = SR // 30                                                   # voice loudness per video frame: the robot's mouth
    rms = np.array([np.sqrt((vo[i:i + hop] ** 2).mean()) for i in range(0, len(vo) - hop, hop)])
    rms = np.convolve(rms, [.25, .5, .25], 'same')
    rms = np.clip(rms / (np.percentile(rms[rms > 1e-3], 95) + 1e-9), 0, 1) if V else rms * 0
    (HERE / f'{name}.timing.js').write_text('window.QUIZ = ' + json.dumps({**Z, 'T': T, 'mouth': [round(float(x), 3) for x in rms]}, ensure_ascii=False) + '\n', encoding='utf-8')
    print('end', T['end'])

if len(sys.argv) > 2 and sys.argv[2] == 'lines':      # write the voice script: quiz/vo/<name>/<i>.txt
    d = HERE / 'vo' / sys.argv[1]; d.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(lines(sys.argv[1])): (d / f'{i}.txt').write_text(s, encoding='utf-8')
    print(len(lines(sys.argv[1])), 'lines')
else:
    build(sys.argv[1])
