# MFE Driverless — Assignment 2: ROS 2 pub / sub over Tailscale

This assignment introduces ROS 2 publishers, subscribers, namespaces, and running nodes together across a **shared class network** using Tailscale. It is split into two parts, [Advent-of-Code style](https://adventofcode.com/): Part 1 is a warm-up, Part 2 is the real challenge.

- **A2.1** — publish `Hello World!` on your own namespaced topic.
- **A2.2** — subscribe to the professor's noisy signal, filter it with a first-order IIR low-pass filter, and publish your filtered output. The professor's grader auto-discovers your topic and reports back on `/professor/feedback` whether you got it right.

Everything runs inside a Docker container so your local OS and Python version don't matter.

---

## 1. Getting started

### 1.1 GitHub
1. Go to this repo on GitHub.
2. Create a new branch named after you, e.g. `NeilJoeGeorge`.
3. Clone and check out your branch:

```bash
git clone <repo-url>
cd Driverless-A2
git checkout <FirstNameLastName>
```

### 1.2 Tailscale (class VPN)
The professor runs a ROS 2 node on the class Tailscale network. Every student joins the same tailnet so DDS discovery works between machines.

1. Install Tailscale: <https://tailscale.com/download>.
2. `sudo tailscale up` and sign in with the invite the professor sent.
3. Verify you can reach the professor's node: `tailscale ping professor` (hostname will be shared in class).
4. Note your own Tailscale hostname/IP — you'll set it via env var below if auto-detection fails.

### 1.3 Docker
Linux host with Docker + Docker Compose is the supported path (host networking + Tailscale interface work cleanly).

```bash
cd docker
export GITHUB_USER=<your-github-handle>          # required
export A2_PROFESSOR_HOST=<professor tailnet host>  # e.g. professor.tail1234.ts.net
docker compose build
docker compose run --rm student
```

Inside the container you'll have `/workspace` mounted to `ros2_ws/`. Build and source:

```bash
cd /workspace
colcon build --symlink-install
source install/setup.bash
```

> **macOS/Windows caveat:** Docker Desktop's `network_mode: host` is limited. If you're not on Linux, run the container with `--network host` on a Linux VM, or use Tailscale's [userspace networking mode](https://tailscale.com/kb/1112/userspace-networking) inside the container. Ask the professor for the current recommendation.

---

## 2. A2.1 — Hello World! (warm-up)

**Goal:** publish the string `Hello World!` on `/${GITHUB_USER}/hello` at 1 Hz.

The template is already written for you in `ros2_ws/src/a2_student/a2_student/hello_publisher.py`. You just need to launch it with your GitHub username as the ROS namespace:

```bash
ros2 launch a2_student hello.launch.py github_user:=$GITHUB_USER
```

The professor's grader is watching for any topic matching `/<user>/hello` (type `std_msgs/String`). When it sees `Hello World!` from your namespace, it will publish on `/professor/feedback`:

```
Congrats <your-github-user>, the answer is correct
```

Watch the feedback live from another terminal (inside the container):
```bash
ros2 topic echo /professor/feedback
```

**Deliverable for A2.1:** a screenshot of `/professor/feedback` congratulating your GitHub handle, committed to your branch under `submissions/a2_1_feedback.png`.

---

## 3. A2.2 — Low-pass filter the professor's signal

The professor publishes a deterministic-but-noisy waveform on `/professor/signal` (`std_msgs/Float32`):

```
x(t) = 1.0 * sin(2π * 0.5 * t) + 0.6 * sin(2π * 5.0 * t) + N(0, 0.3²)
```

Your job is to **subscribe** to it, apply a **first-order IIR low-pass filter**, and **publish** the filtered value on `/${GITHUB_USER}/answer` (`std_msgs/Float32`).

### The filter (exact spec — do not change α)

```
y[n] = α · x[n] + (1 − α) · y[n − 1]
y[0] = x[0]
α    = 0.1
```

This is the same "exponential moving average" you'll see in most sensor pipelines. Theory refs:
- Wikipedia — [Infinite impulse response](https://en.wikipedia.org/wiki/Infinite_impulse_response) and [Exponential smoothing](https://en.wikipedia.org/wiki/Exponential_smoothing).
- Smith, *The Scientist and Engineer's Guide to DSP*, [Ch. 19 — Recursive Filters](https://www.dspguide.com/ch19.htm) (free online).

### Where to put your code
Open `ros2_ws/src/a2_student/a2_student/lpf_node.py`. There's a `TODO` block inside `_on_signal`. Replace the stub with the IIR recurrence above.

### Run it
```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch a2_student lpf.launch.py github_user:=$GITHUB_USER
```

### How grading works
The professor's grader:
1. Subscribes to `/professor/signal` and runs **the same** LPF (α = 0.1, y[0] = x[0]) to build a reference sequence.
2. Discovers any `/<user>/answer` topic on the network and buffers the last 200 samples per student.
3. Matches student samples to the reference by nearest receive-time and computes MSE.
4. If MSE < 0.02, publishes on `/professor/feedback`:
   ```
   Congrats <your-github-user>, the answer is correct (MSE=0.0034)
   ```
   Otherwise:
   ```
   Sorry <your-github-user>, the answer is incorrect (MSE=0.4127)
   ```

Feedback is only republished when your verdict changes, so if your filter is wrong you'll only see one "incorrect" message per attempt.

**Deliverable for A2.2:** screenshot of `/professor/feedback` congratulating your handle, committed as `submissions/a2_2_feedback.png`, plus your finished `lpf_node.py`.

---

## 4. Topic contract (summary)

| Topic                 | Type              | Owner    | Purpose                           |
| --------------------- | ----------------- | -------- | --------------------------------- |
| `/professor/signal`   | `std_msgs/Float32` | Professor | Noisy input for A2.2              |
| `/professor/feedback` | `std_msgs/String`  | Professor | Per-student grading verdict       |
| `/<user>/hello`       | `std_msgs/String`  | Student  | A2.1 output                       |
| `/<user>/answer`      | `std_msgs/Float32` | Student  | A2.2 output (your filtered signal) |

---

## 5. Layout

```
Driverless-A2/
├── docker/                    # Dockerfile, compose, CycloneDDS config, entrypoint
├── ros2_ws/
│   └── src/
│       ├── a2_student/        # your template — this is where you write code
│       └── a2_professor/      # for reference; not run by students
└── README.md
```

## 6. Troubleshooting

- **`ros2 topic list` doesn't show `/professor/signal`.** DDS discovery isn't reaching the professor. Confirm `tailscale ping <professor-host>` works, that `A2_PROFESSOR_HOST` is set, and that `ROS_DOMAIN_ID` matches (`42`).
- **You see your own topics but no one else's.** Check `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` inside the container (`env | grep RMW`).
- **Grader keeps saying incorrect.** Confirm α = 0.1, that you initialise `y[0] = x[0]` (not zero), and that you're publishing on `/<GITHUB_USER>/answer` (not `~answer` or `/answer`).

---

## 7. Submission
1. Commit your changes to your `FirstNameLastName` branch.
2. Include both feedback screenshots in `submissions/`.
3. Open a pull request against `main` when done.
