# MFE Driverless — Assignment 2: ROS 2 pub / sub with Local Grading

This assignment introduces ROS 2 publishers, subscribers, namespaces, and DDS discovery. It is split into two parts: Part 1 is a warm-up, Part 2 is the real challenge.

- **A2.1** — publish `Hello World!` on your own namespaced topic.
- **A2.2** — subscribe to a noisy signal, filter it with a first-order IIR low-pass filter, and publish your filtered output. The grader runs locally alongside your code and auto-discovers your topic, reporting back on `/grader/feedback` whether you got it right.

Everything runs inside a Docker container using `docker-compose-local.yml`.

> **Grading Setup** — The grader runs as a local Docker service alongside your student code. Both use host networking and ROS domain ID 42 for automatic DDS discovery.

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

### 1.2 Docker & Local Grading
The grader runs as a local service inside Docker alongside your student code. Both use host networking and ROS domain ID 42 for automatic DDS discovery.

```bash
cd docker
docker compose -f docker-compose-local.yml build
docker compose -f docker-compose-local.yml up -d
```

This starts two services:
1. **student** — your code (subscriber + publisher)
2. **grader** — reference implementation (signal publisher + grader)

Both services share the same network and ROS domain, so topics auto-discover via DDS.

Inside either container, the workspace is mounted at `/workspace` (your `ros2_ws`). Build and source:

```bash
cd /workspace
colcon build --symlink-install
source install/setup.bash
```

View logs from either service:
```bash
docker compose -f docker-compose-local.yml logs student -f  # tail student logs
docker compose -f docker-compose-local.yml logs grader -f   # tail grader logs
docker compose -f docker-compose-local.yml logs             # both services
```

Stop everything:
```bash
docker compose -f docker-compose-local.yml down
```

---

## 2. A2.1 — Hello World! (warm-up)

**Goal:** publish the string `Hello World!` on `/${GITHUB_USER}/hello` at 1 Hz.

Open `ros2_ws/src/a2_new_member/a2_new_member/hello_publisher.py`. The node, publisher, and timer are already wired up — there's a `TODO` block inside `_tick` where you build and publish a `std_msgs/String`. If you're new to ROS 2 publishers, see the [ROS2 Industrial Workshop — Simple Publisher/Subscriber](https://ros2-industrial-workshop.readthedocs.io/en/latest/_source/basics/ROS2-Simple-Publisher-Subscriber.html). Then launch it with your GitHub username as the ROS namespace:

```bash
ros2 launch a2_new_member hello.launch.py github_user:=$GITHUB_USER
```

The grader watches for any topic matching `/<user>/hello` (type `std_msgs/String`). When it sees `Hello World!` from your namespace, it responds on `/grader/feedback`:

```
Hello <your-github-user>, I see your hello world
```

Watch the feedback live from another terminal (inside the container):
```bash
ros2 topic echo /grader/feedback
```

Grader confirms A2.1 is working when you see the personalized hello message.

---

## 3. A2.2 — Low-pass filter Neil's signal

Neil publishes a deterministic-but-noisy waveform on `/grader/signal` (`std_msgs/Float32`):

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
Open `ros2_ws/src/a2_new_member/a2_new_member/lpf_node.py`. There's a `TODO` block inside `_on_signal`. Replace the stub with the IIR recurrence above.

### Run it
```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch a2_new_member lpf.launch.py github_user:=$GITHUB_USER
```

Watch the grading feedback in another terminal:
```bash
ros2 topic echo /grader/feedback
```

**Grading criteria:**
- Grader runs reference LPF (α = 0.1) on `/grader/signal`
- Subscribes to `/<user>/answer` and buffers samples
- Computes MSE between your output and reference
- Publishes continuous feedback: `Congrats <user>, the answer is correct (MSE=0.007)`

Feedback updates every ~2 seconds, so fix your filter and watch it update in real-time.

---

## 4. Visualizing with Foxglove Studio (optional but strongly recommended)

Seeing the raw signal and your filtered signal on the same plot makes it obvious what your filter is doing wrong.

### 4.1 Install the Foxglove bridge inside the container
Already available in the image:
```bash
apt-get install -y ros-humble-foxglove-bridge   # only if you rebuild the image
ros2 run foxglove_bridge foxglove_bridge port:=8765
```
Leave that terminal running.

### 4.2 Install Foxglove Studio on your host
Download from <https://foxglove.dev/download> (free, works on Linux/macOS/Windows).

### 4.3 Connect
1. Open Foxglove Studio → **Open connection…** → **Foxglove WebSocket**.
2. URL: `ws://localhost:8765` (or `ws://<host-ip>:8765` from another machine).
3. Add a **Plot** panel.
   - Series 1: topic `/grader/signal`, path `data`, color red.
   - Series 2: topic `/${GITHUB_USER}/answer`, path `data`, color green.
4. Add a **Raw Messages** panel on `/grader/feedback` to see verdicts as they arrive.

You should see the green (filtered) curve tracking the low-frequency component of the red (noisy) signal while attenuating the 5 Hz sinusoid — that's the LPF working.

> Tip: save your Foxglove layout to `submissions/a2_layout.json` (**Layout → Export**) so future assignments can reuse it.

---

## 5. Topic contract (summary)

| Topic              | Type              | Owner   | Purpose                            |
| ------------------ | ----------------- | ------- | ---------------------------------- |
| `/grader/signal`     | `std_msgs/Float32` | Neil    | Noisy input for A2.2               |
| `/grader/feedback`   | `std_msgs/String`  | Neil    | Per-student grading verdict        |
| `/<user>/hello`    | `std_msgs/String`  | Student | A2.1 output                        |
| `/<user>/answer`   | `std_msgs/Float32` | Student | A2.2 output (your filtered signal) |

---

## 6. Layout

```
Driverless-A2/
├── docker/
│   ├── docker-compose-local.yml  # Two services: student + grader
│   ├── Dockerfile                # ROS2 Humble + dependencies
│   ├── entrypoint.sh             # Startup script (socket buffer config)
│   └── cyclonedds.xml            # DDS discovery config
├── ros2_ws/
│   └── src/
│       ├── a2_new_member/        # your template — write code here
│       └── a2_grader/            # grader (runs as local service in docker-compose)
│           ├── a2_grader/        # Python package
│           ├── config/           # params.yaml
│           ├── launch/           # neil.launch.py
│           ├── setup.py
│           └── package.xml
└── README.md
```

## 7. Troubleshooting

- **`ros2 topic list` doesn't show `/grader/signal`.** Ensure both grader and student are running in the container. Check `docker compose logs`.
- **Topics visible but grader shows no feedback.** Verify your nodes are publishing to correct topics (`/<user>/hello` and `/<user>/answer`).
- **Grader keeps saying incorrect.** Confirm α = 0.1, initialize `y[0] = x[0]` (not zero), and publishing on `/<GITHUB_USER>/answer`.

---

## 8. Submission Checklist

- [ ] `hello_publisher.py` publishes `"Hello World!"` at 1 Hz on `/<user>/hello`
- [ ] `lpf_node.py` implements IIR filter with α=0.1 on `/<user>/answer`
- [ ] Both nodes launch automatically via `bringup.launch.py`
- [ ] Grader feedback confirms both A2.1 and A2.2 are working
- [ ] Code is committed to your branch

---

## 9. Parameters

Scenario constants are exposed as ROS parameters loaded from YAML at launch time:

- **Grader** [`ros2_ws/src/a2_grader/config/params.yaml`](ros2_ws/src/a2_grader/config/params.yaml):
  - Signal: `signal_hz`, `f1`, `a1`, `f2`, `a2`, `noise_std`, `seed`
  - Grading: `alpha`, `match_window`, `mse_tolerance`, `discovery_period_s`, `grade_period_s`

- **Student** [`ros2_ws/src/a2_new_member/config/params.yaml`](ros2_ws/src/a2_new_member/config/params.yaml):
  - `alpha` (fixed at `0.1` for grading; do **not** change)

Launch files automatically load parameters via the `parameters=[...]` argument.

