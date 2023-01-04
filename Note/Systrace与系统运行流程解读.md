# Systrace和perfetto信息解读

## 线程状态查看

- 绿色是running，表示正在运行，进行对比的时候需要验证以下几个问题
  1. 是否是频率不够
  2. 是否跑在了小核上
  3. 是否频繁切换Running和Runnable
  4. 是否频繁切换Running和sleep
  5. 是否跑在了不该跑的核上，比如不重要的线程占用了大核

- 蓝色是Runnable，可以运行但是在等待cpu调度

- 白色是休眠，可能是因为线程在互斥锁上被阻塞

- 橘色是不可中断的睡眠态，（Uninterruptible Sleep-IO Block），如果有大量的橘色不可中断的睡眠态出现，那么一般是由于进入了低内存状态，申请内存的时候触发 pageFault, linux 系统的 page cache 链表中有时会出现一些还没准备好的 page(即还没把磁盘中的内容完全地读出来) , 而正好此时用户在访问这个 page 时就会出现 wait_on_page_locked_killable 阻塞了. 只有系统当 io 操作很繁忙时, 每笔的 io 操作都需要等待排队时, 极其容易出现且阻塞的时间往往会比较长。

- 棕色（Systrace是紫色）的是不可中断的睡眠态（Uninterruptible Sleep-non IO Block)

## 线程唤醒信息分析

### systrace

​		一个常见的情况是：应用主线程程使用 Binder 与 SystemServer 的 AMS 进行通信，但是恰好 AMS 的这个函数正在等待锁释放（或者这个函数本身执行时间很长），那么应用主线程就需要等待比较长的时间，那么就会出现性能问题，比如响应慢或者卡顿，这就是为什么后台有大量的进程在运行，或者跑完 Monkey 之后，整机性能会下降的一个主要原因

​		另外一个场景的情况是：应用主线程在等待此应用的其他线程执行的结果，这时候线程唤醒信息就可以用来分析主线程到底被哪个线程 Block 住了，比如下面这个场景，这一帧 doFrame 执行了 152ms，有明显的异常，但是大部分时间是在 sleep

[![image-20211210185851589](https://androidperformance.com/images/Android-Systrace-Pre/image-20211210185851589.png)](https://androidperformance.com/images/Android-Systrace-Pre/image-20211210185851589.png)

这时候放大来看，可以看到是一段一段被唤醒的，这时候点击图中的 runnable ，下面的信息区就会出现唤醒信息，可以顺着看这个线程到底在做什么

[![image-20211213145728467](https://androidperformance.com/images/Android-Systrace-Pre/image-20211213145728467.png)](https://androidperformance.com/images/Android-Systrace-Pre/image-20211213145728467.png)

20424 线程是 RenderHeartbeat，这就牵扯到了 App 自身的代码逻辑，需要 App 自己去分析 RenderHeartbeat 到底做了什么事情

[![image-20211210190921614](https://androidperformance.com/images/Android-Systrace-Pre/image-20211210190921614.png)](https://androidperformance.com/images/Android-Systrace-Pre/image-20211210190921614.png)

Systrace 可以标示出这个的一个原因是，一个任务在进入 Running 状态之前，会先进入 Runnable 状态进行等待，而 Systrace 会把这个状态也标示在 Systrace 上（非常短，需要放大进行看）

[![img](https://androidperformance.com/images//15638916556947.jpg)](https://androidperformance.com/images//15638916556947.jpg)

拉到最上面查看对应的 cpu 上的 taks 信息，会标识这个 task 在被唤醒之前的状态：
[![img](https://androidperformance.com/images//15638916674736.jpg)](https://androidperformance.com/images//15638916674736.jpg)

顺便贴一下 Linux 常见的进程状态

1. **D** 无法中断的休眠状态（通常 IO 的进程）；
2. **R** 正在可运行队列中等待被调度的；
3. **S** 处于休眠状态；
4. **T** 停止或被追踪；
5. **W** 进入内存交换 （从内核2.6开始无效）；
6. **X** 死掉的进程 （基本很少見）；
7. **Z** 僵尸进程；
8. **<** 优先级高的进程
9. **N** 优先级较低的进程
10. **L** 有些页被锁进内存
11. **s** 进程的领导者（在它之下有子进程）
12. **l** 多进程的（使用 CLONE_THREAD, 类似 NPTL pthreads）
13. **+** 位于后台的进程组

### Perfetto

- 如何查看线程唤醒端:

在systrace上,我们一般是通过查看Runnable状态中的wakeup from,然后自己滑到对应的线程区域,如果线程之间唤醒关系比较长,那寻找起来未免太繁琐.

Perfetto的操作方式不同,我们只需要点击Runnable后的Running状态,然后点击下方的跳转按钮,

![img](https://img-blog.csdnimg.cn/img_convert/c03c02f963962b53edf17b73c7e167e1.png)

这会自动跳转到线程调度区域中的对应轨道中,并且下方会显示当前线程的唤醒端(♦) 以及此次唤醒的调度延迟时间:

![img](https://img-blog.csdnimg.cn/img_convert/6498e375934adc3521e67ff1f650fd14.png)

选中唤醒端线程对应的slice,然后同样点击跳转按钮:

![img](https://img-blog.csdnimg.cn/img_convert/219ff776b80cfb021dd4105820f5acdf.png)

即可跳转回对应的进程区域的轨道中:

![img](https://img-blog.csdnimg.cn/img_convert/38f2975618f91e586798451b3f8df820.png)



## 函数Slice信息解析

![img](https://androidperformance.com/images//15638916944506.jpg)

## Counter Sample 信息解析

[![img](https://androidperformance.com/images//15638917076247.jpg)](https://androidperformance.com/images//15638917076247.jpg)

## Async Slice 信息解析

[![img](https://androidperformance.com/images//15638917151530.jpg)](https://androidperformance.com/images//15638917151530.jpg)

## CPU Slice 信息解析

[![img](https://androidperformance.com/images//15638917222302.jpg)](https://androidperformance.com/images//15638917222302.jpg)

## User Expectation 信息解析

位于整个 Systrace 最上面的部分,标识了 Rendering Response 和 Input Response
[![img](https://androidperformance.com/images//15638917348214.jpg)](https://androidperformance.com/images//15638917348214.jpg)



# SystemServer进程

​		窗口归SystemServer管理，其中有两个比较重要的线程，Android.Anim和Android.Anim.if

这里我们以**应用启动**为例，查看窗口时如何在两个线程之间进行切换(Android P 里面，应用的启动动画由 Launcher 和应用自己的第一帧组成，之前是在 SystemServer 里面的，现在多任务的动画为了性能部分移到了 Launcher 去实现)

首先我们点击图标启动应用的时候，由于 App 还在启动，Launcher 首先启动一个 StartingWindow，等 App 的第一帧绘制好了之后，再切换到 App 的窗口动画

Launcher 动画
[![-w1019](https://androidperformance.com/images/15811380751710.jpg)](https://androidperformance.com/images/15811380751710.jpg)

此时对应的，App 正在启动
[![-w1025](https://androidperformance.com/images/15811380510520.jpg)](https://androidperformance.com/images/15811380510520.jpg)

从上图可以看到，应用第一帧已经准备好了，接下来看对应的 SystemServer ，可以看到应用启动第一帧绘制完成后，动画切换到 App 的 Window 动画

[![-w1236](https://androidperformance.com/images/15811383348116.jpg)](https://androidperformance.com/images/15811383348116.jpg)

## ActivityManagerService

AMS 和 WMS 算是 SystemServer 中最繁忙的两个 Service 了，与 AMS 相关的 Trace 一般会用 TRACE_TAG_ACTIVITY_MANAGER 这个 TAG，在 Systrace 中的名字是 ActivityManager

下面是启动一个新的进程的时候，AMS 的输出
[![-w826](https://androidperformance.com/images/15808922537197.jpg)](https://androidperformance.com/images/15808922537197.jpg)

在进程和四大组件的各种场景一般都会有对应的 Trace 点来记录，比如大家熟悉的 ActivityStart、ActivityResume、activityStop 等，这些 Trace 点有一些在应用进程，有一些在 SystemServer 进程，所以大家在看 Activity 相关的代码逻辑的时候，需要不断在这两个进程之间进行切换，这样才能从一个整体的角度来看应用的状态变化和 SystemServer 在其中起到的作用。
[![-w660](https://androidperformance.com/images/15808919921881.jpg)](https://androidperformance.com/images/15808919921881.jpg)

## WindowManagerService

与 WMS 相关的 Trace 一般会用 TRACE_TAG_WINDOW_MANAGER 这个 TAG，在 Systrace 中 WindowManagerService 在 SystemServer 中多在对应的 Binder 中出现，比如下面应用启动的时候，relayoutWindow 的 Trace 输出

[![-w957](https://androidperformance.com/images/15808923853151.jpg)](https://androidperformance.com/images/15808923853151.jpg)

在 Window 的各种场景一般都会有对应的 Trace 点来记录，比如大家熟悉的 relayoutWIndow、performLayout、prepareToDisplay 等
[![-w659](https://androidperformance.com/images/15808918520410.jpg)](https://androidperformance.com/images/15808918520410.jpg)

# Input

Input是SystemServer的线程里面非常中重要的一部分，主要是有InputReader和InputDispatcher这两个Native线程组成，

1. **InputReader** 负责从 EventHub 里面把 Input 事件读取出来，然后交给 InputDispatcher 进行事件分发
2. **InputDispatcher** 在拿到 InputReader 获取的事件之后，对事件进行包装和分发 (也就是发给对应的)
3. **OutboundQueue** 里面放的是即将要被派发给对应 AppConnection 的事件
4. **WaitQueue** 里面记录的是已经派发给 AppConnection 但是 App 还在处理没有返回处理成功的事件
5. **PendingInputEventQueue** 里面记录的是 App 需要处理的 Input 事件，这里可以看到已经到了应用进程
6. **deliverInputEvent** 标识 App UI Thread 被 Input 事件唤醒
7. **InputResponse** 标识 Input 事件区域，这里可以看到一个 Input_Down 事件 + 若干个 Input_Move 事件 + 一个 Input_Up 事件的处理阶段都被算到了这里
8. **App 响应 Input 事件** ： 这里是滑动然后松手，也就是我们熟悉的桌面滑动的操作，桌面随着手指的滑动更新画面，松手后触发 Fling 继续滑动，从 Systrace 就可以看到整个事件的流程

下面以第一个 Input_Down 事件的处理流程来进行详细的工作流说明，其他的 Move 事件和 Up 事件的处理是一样的（部分不一样，不过影响不大）

## InputDown 事件在 SystemServer 的工作流

放大 SystemServer 的部分，可以看到其工作流(蓝色)，**滑动桌面包括 Input_Down + 若干个 Input_Move + Input_Up ，我们这里看的是 Input_Down 这个事件**

[![img](https://androidperformance.com/images/15728723576583.jpg)](https://androidperformance.com/images/15728723576583.jpg)

## InputDown 事件在 App 的工作流

应用在收到 Input 事件后，有时候会马上去处理 (没有 Vsync 的情况下)，有时候会等 Vsync 信号来了之后去处理，这里 Input_Down 事件就是直接去唤醒主线程做处理，其 Systrace 比较简单，最上面有个 Input 事件队列，主线程则是简单的处理

[![img](https://androidperformance.com/images/15728723679523.jpg)](https://androidperformance.com/images/15728723679523.jpg)

### App 的 Pending 队列

[![img](https://androidperformance.com/images/15728723758398.jpg)](https://androidperformance.com/images/15728723758398.jpg)

### 主线程处理 Input 事件

主线程处理 Input 事件这个大家比较熟悉，从下面的调用栈可以看到，Input 事件传到了 ViewRootImpl，最终到了 DecorView ，然后就是大家熟悉的 Input 事件分发机制

[![img](C:\Users\zjiang.li\Desktop\15728723834004.jpg)](https://androidperformance.com/images/15728723834004.jpg)



### Input事件基本流向

1. **InputReader 读取 Input 事件**
2. **InputReader 将读取的 Input 事件放到 InboundQueue 中**
3. **InputDispatcher 从 InboundQueue 中取出 Input 事件派发到各个 App(连接) 的 OutBoundQueue**
4. **同时将事件记录到各个 App(连接) 的 WaitQueue**
5. **App 接收到 Input 事件，同时记录到 PendingInputEventQueue ，然后对事件进行分发处理**
6. **App 处理完成后，回调 InputManagerService 将负责监听的 WaitQueue 中对应的 Input 移除**

通过上面的流程，一次 Input 事件就被消耗掉了(当然这只是正常情况，还有很多异常情况、细节处理，这里就不细说了，自己看相关流程的时候可以深挖一下) ， 那么本节就从上面的关键流中取几个重要的知识点讲解（部分流程和图参考和拷贝了 Gityuan 的博客的图，链接在最下面**参考**那一节）

## InputReader

InputReader 是一个 Native 线程，跑在 SystemServer 进程里面，其核心功能是从 EventHub 读取事件、进行加工、将加工好的事件发送到 InputDispatcher

InputReader Loop 流程如下

1. getEvents：通过 EventHub (监听目录 /dev/input )读取事件放入 mEventBuffer ,而mEventBuffer 是一个大小为256的数组, 再将事件 input_event 转换为 RawEvent
2. processEventsLocked: 对事件进行加工, 转换 RawEvent -> NotifyKeyArgs(NotifyArgs)
3. QueuedListener->flush：将事件发送到 InputDispatcher 线程, 转换 NotifyKeyArgs -> KeyEntry(EventEntry)

核心代码 loopOnce 处理流程如下：
[![img](https://androidperformance.com/images/15728723980792.jpg)](https://androidperformance.com/images/15728723980792.jpg)

InputReader 核心 Loop 函数 loopOnce 逻辑如下

```c++
void InputReader::loopOnce() {
    int32_t oldGeneration;
    int32_t timeoutMillis;
    bool inputDevicesChanged = false;
    std::vector<InputDeviceInfo> inputDevices;
    { // acquire lock
    ......
    //获取输入事件、设备增删事件，count 为事件数量
    size_t count = mEventHub ->getEvents(timeoutMillis, mEventBuffer, EVENT_BUFFER_SIZE);
    {
    ......
        if (count) {//处理事件
            processEventsLocked(mEventBuffer, count);
        }

    }
    ......
    mQueuedListener->flush();//将事件传到 InputDispatcher，这里getListener 得到的就是 InputDispatcher
}
```

## InputDispatcher

上面的 InputReader 调用 mQueuedListener->flush 之后 ，将 Input 事件加入到InputDispatcher 的 mInboundQueue ，然后唤醒 InputDispatcher ， 从 Systrace 的唤醒信息那里也可以看到 InputDispatch 线程是被 InputReader 唤醒的

[![img](https://androidperformance.com/images/15728724564781.jpg)](https://androidperformance.com/images/15728724564781.jpg)

InputDispatcher 的核心逻辑如下：

1. dispatchOnceInnerLocked(): 从 InputDispatcher 的 mInboundQueue 队列，取出事件 EventEntry。另外该方法开始执行的时间点 (currentTime) 便是后续事件 dispatchEntry 的分发时间 (deliveryTime）
2. dispatchKeyLocked()：满足一定条件时会添加命令 doInterceptKeyBeforeDispatchingLockedInterruptible；
3. enqueueDispatchEntryLocked()：生成事件 DispatchEntry 并加入 connection 的 outbound 队列
4. startDispatchCycleLocked()：从 outboundQueue 中取出事件 DispatchEntry, 重新放入 connection 的 waitQueue 队列；
5. InputChannel.sendMessage 通过 socket 方式将消息发送给远程进程；
6. runCommandsLockedInterruptible()：通过循环遍历的方式，依次处理 mCommandQueue 队列中的所有命令。而 mCommandQueue 队列中的命令是通过 postCommandLocked() 方式向该队列添加的。

[![img](https://androidperformance.com/images/15728724685263.jpg)](https://androidperformance.com/images/15728724685263.jpg)

其核心处理逻辑在 dispatchOnceInnerLocked 这里

```c++
void InputDispatcher::dispatchOnceInnerLocked(nsecs_t* nextWakeupTime) {
    // Ready to start a new event.
    // If we don't already have a pending event, go grab one.
    if (! mPendingEvent) {
        if (mInboundQueue.isEmpty()) {
        } else {
            // Inbound queue has at least one entry.
            mPendingEvent = mInboundQueue.dequeueAtHead();
            traceInboundQueueLengthLocked();
        }

        // Poke user activity for this event.
        if (mPendingEvent->policyFlags & POLICY_FLAG_PASS_TO_USER) {
            pokeUserActivityLocked(mPendingEvent);
        }

        // Get ready to dispatch the event.
        resetANRTimeoutsLocked();
    }
    case EventEntry::TYPE_MOTION: {
        done = dispatchMotionLocked(currentTime, typedEntry,
                &dropReason, nextWakeupTime);
        break;
    }

    if (done) {
        if (dropReason != DROP_REASON_NOT_DROPPED) {
            dropInboundEventLocked(mPendingEvent, dropReason);
        }
        mLastDropReason = dropReason;
        releasePendingEventLocked();
        *nextWakeupTime = LONG_LONG_MIN;  // force next poll to wake up immediately
    }
}
```

## Input 刷新与 Vsync

Input 的刷新取决于触摸屏的采样，目前比较多的屏幕采样率是 120Hz 和 160Hz ，对应就是 8ms 采样一次或者 6.25ms 采样一次，我们来看一下其在 Systrace 上的展示

[![img](https://androidperformance.com/images/15728725296687.jpg)](https://androidperformance.com/images/15728725296687.jpg)

可以看到上图中， InputReader 每隔 6.25ms 就可以读上来一个数据，交给 InputDispatcher 去分发给 App ，那么是不是屏幕采样率越高越好呢？也不一定，比如上面那张图，虽然 InputReader 每隔 6.25ms 就可以读上来一个数据给 InputDispatcher 去分发给 App ，但是从 WaitQueue 的表现来看，应用并没有消耗这个 Input 事件，这是为什么呢？

原因在于应用消耗 Input 事件的时机是 Vsync 信号来了之后，刷新率为 60Hz 的屏幕，一般系统也是 60 fps ，也就是说两个 Vsync 的间隔在 16.6ms ，这期间如果有两个或者三个 Input 事件，那么必然有一个或者两个要被抛弃掉，只拿最新的那个。也就是说：

1. **在屏幕刷新率和系统 FPS 都是 60 的时候，盲目提高触摸屏的采样率，是没有太大的效果的，反而有可能出现上面图中那样，有的 Vsync 周期中有两个 Input 事件，而有的 Vsync 周期中有三个 Input 事件，这样造成事件不均匀，可能会使 UI 产生抖动**
2. **在屏幕刷新率和系统 FPS 都是 60 的时候，使用 120Hz 采样率的触摸屏就可以了**
3. **如果在屏幕刷新率和系统 FPS 都是 90 的时候 ，那么 120Hz 采样率的触摸屏显然不够用了，这时候应该采用 180Hz 采样率的屏幕**

## Input 调试信息

Dumpsys Input 主要是 Debug 用，我们也可以来看一下其中的一些关键信息，到时候遇到了问题也可以从这里面找 ， 其命令如下：

```
adb shell dumpsys input
```

其中的输出比较多，我们终点截取 Device 信息、InputReader、InputDispatcher 三段来看就可以了

### Device 信息

主要是目前连接上的 Device 信息，下面摘取的是 touch 相关的

```
    3: main_touch
      Classes: 0x00000015
      Path: /dev/input/event6
      Enabled: true
      Descriptor: 4055b8a032ccf50ef66dbe2ff99f3b2474e9eab5
      Location: main_touch/input0
      ControllerNumber: 0
      UniqueId: 
      Identifier: bus=0x0000, vendor=0xbeef, product=0xdead, version=0x28bb
      KeyLayoutFile: /system/usr/keylayout/main_touch.kl
      KeyCharacterMapFile: /system/usr/keychars/Generic.kcm
      ConfigurationFile: 
      HaveKeyboardLayoutOverlay: false
```

### Input Reader 状态

InputReader 这里就是当前 Input 事件的一些展示

```
  Device 3: main_touch
    Generation: 24
    IsExternal: false
    HasMic:     false
    Sources: 0x00005103
    KeyboardType: 1
    Motion Ranges:
      X: source=0x00005002, min=0.000, max=1079.000, flat=0.000, fuzz=0.000, resolution=0.000
      Y: source=0x00005002, min=0.000, max=2231.000, flat=0.000, fuzz=0.000, resolution=0.000
      PRESSURE: source=0x00005002, min=0.000, max=1.000, flat=0.000, fuzz=0.000, resolution=0.000
      SIZE: source=0x00005002, min=0.000, max=1.000, flat=0.000, fuzz=0.000, resolution=0.000
      TOUCH_MAJOR: source=0x00005002, min=0.000, max=2479.561, flat=0.000, fuzz=0.000, resolution=0.000
      TOUCH_MINOR: source=0x00005002, min=0.000, max=2479.561, flat=0.000, fuzz=0.000, resolution=0.000
      TOOL_MAJOR: source=0x00005002, min=0.000, max=2479.561, flat=0.000, fuzz=0.000, resolution=0.000
      TOOL_MINOR: source=0x00005002, min=0.000, max=2479.561, flat=0.000, fuzz=0.000, resolution=0.000
    Keyboard Input Mapper:
      Parameters:
        HasAssociatedDisplay: false
        OrientationAware: false
        HandlesKeyRepeat: false
      KeyboardType: 1
      Orientation: 0
      KeyDowns: 0 keys currently down
      MetaState: 0x0
      DownTime: 521271703875000
    Touch Input Mapper (mode - direct):
      Parameters:
        GestureMode: multi-touch
        DeviceType: touchScreen
        AssociatedDisplay: hasAssociatedDisplay=true, isExternal=false, displayId=''
        OrientationAware: true
      Raw Touch Axes:
        X: min=0, max=1080, flat=0, fuzz=0, resolution=0
        Y: min=0, max=2232, flat=0, fuzz=0, resolution=0
        Pressure: min=0, max=127, flat=0, fuzz=0, resolution=0
        TouchMajor: min=0, max=512, flat=0, fuzz=0, resolution=0
        TouchMinor: unknown range
        ToolMajor: unknown range
        ToolMinor: unknown range
        Orientation: unknown range
        Distance: unknown range
        TiltX: unknown range
        TiltY: unknown range
        TrackingId: min=0, max=65535, flat=0, fuzz=0, resolution=0
        Slot: min=0, max=20, flat=0, fuzz=0, resolution=0
      Calibration:
        touch.size.calibration: geometric
        touch.pressure.calibration: physical
        touch.orientation.calibration: none
        touch.distance.calibration: none
        touch.coverage.calibration: none
      Affine Transformation:
        X scale: 1.000
        X ymix: 0.000
        X offset: 0.000
        Y xmix: 0.000
        Y scale: 1.000
        Y offset: 0.000
      Viewport: displayId=0, orientation=0, logicalFrame=[0, 0, 1080, 2232], physicalFrame=[0, 0, 1080, 2232], deviceSize=[1080, 2232]
      SurfaceWidth: 1080px
      SurfaceHeight: 2232px
      SurfaceLeft: 0
      SurfaceTop: 0
      PhysicalWidth: 1080px
      PhysicalHeight: 2232px
      PhysicalLeft: 0
      PhysicalTop: 0
      SurfaceOrientation: 0
      Translation and Scaling Factors:
        XTranslate: 0.000
        YTranslate: 0.000
        XScale: 0.999
        YScale: 1.000
        XPrecision: 1.001
        YPrecision: 1.000
        GeometricScale: 0.999
        PressureScale: 0.008
        SizeScale: 0.002
        OrientationScale: 0.000
        DistanceScale: 0.000
        HaveTilt: false
        TiltXCenter: 0.000
        TiltXScale: 0.000
        TiltYCenter: 0.000
        TiltYScale: 0.000
      Last Raw Button State: 0x00000000
      Last Raw Touch: pointerCount=1
        [0]: id=0, x=660, y=1338, pressure=44, touchMajor=44, touchMinor=44, toolMajor=0, toolMinor=0, orientation=0, tiltX=0, tiltY=0, distance=0, toolType=1, isHovering=false
      Last Cooked Button State: 0x00000000
      Last Cooked Touch: pointerCount=1
        [0]: id=0, x=659.389, y=1337.401, pressure=0.346, touchMajor=43.970, touchMinor=43.970, toolMajor=43.970, toolMinor=43.970, orientation=0.000, tilt=0.000, distance=0.000, toolType=1, isHovering=false
      Stylus Fusion:
        ExternalStylusConnected: false
        External Stylus ID: -1
        External Stylus Data Timeout: 9223372036854775807
      External Stylus State:
        When: 9223372036854775807
        Pressure: 0.000000
        Button State: 0x00000000
        Tool Type: 0
```

### InputDispatcher 状态

InputDispatcher 这里的重要信息主要包括er

1. FocusedApplication ：当前获取焦点的应用
2. FocusedWindow ： 当前获取焦点的窗口
3. TouchStatesByDisplay
4. Windows ：所有的 Window
5. MonitoringChannels ：Window 对应的 Channel
6. Connections ：所有的连接
7. AppSwitch: not pending
8. Configuration

```    
Input Dispatcher State:
  DispatchEnabled: 1
  DispatchFrozen: 0
  FocusedApplication: name='AppWindowToken{ac6ec28 token=Token{a38a4b ActivityRecord{7230f1a u0 com.meizu.flyme.launcher/.Launcher t13}}}', dispatchingTimeout=5000.000ms
  FocusedWindow: name='Window{3c007ad u0 com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher}'
  TouchStatesByDisplay:
    0: down=true, split=true, deviceId=3, source=0x00005002
      Windows:
        0: name='Window{3c007ad u0 com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher}', pointerIds=0x80000000, targetFlags=0x105
        1: name='Window{8cb8f7 u0 com.android.systemui.ImageWallpaper}', pointerIds=0x0, targetFlags=0x4102
  Windows:
    2: name='Window{ba2fc6b u0 NavigationBar}', displayId=0, paused=false, hasFocus=false, hasWallpaper=false, visible=true, canReceiveKeys=false, flags=0x21840068, type=0x000007e3, layer=0, frame=[0,2136][1080,2232], scale=1.000000, touchableRegion=[0,2136][1080,2232], inputFeatures=0x00000000, ownerPid=26514, ownerUid=10033, dispatchingTimeout=5000.000ms
    3: name='Window{72b7776 u0 StatusBar}', displayId=0, paused=false, hasFocus=false, hasWallpaper=false, visible=true, canReceiveKeys=false, flags=0x81840048, type=0x000007d0, layer=0, frame=[0,0][1080,84], scale=1.000000, touchableRegion=[0,0][1080,84], inputFeatures=0x00000000, ownerPid=26514, ownerUid=10033, dispatchingTimeout=5000.000ms
    9: name='Window{3c007ad u0 com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher}', displayId=0, paused=false, hasFocus=true, hasWallpaper=true, visible=true, canReceiveKeys=true, flags=0x81910120, type=0x00000001, layer=0, frame=[0,0][1080,2232], scale=1.000000, touchableRegion=[0,0][1080,2232], inputFeatures=0x00000000, ownerPid=27619, ownerUid=10021, dispatchingTimeout=5000.000ms
  MonitoringChannels:
    0: 'WindowManager (server)'
  RecentQueue: length=10
    MotionEvent(deviceId=3, source=0x00005002, action=MOVE, actionButton=0x00000000, flags=0x00000000, metaState=0x00000000, buttonState=0x00000000, edgeFlags=0x00000000, xPrecision=1.0, yPrecision=1.0, displayId=0, pointers=[0: (524.5, 1306.4)]), policyFlags=0x62000000, age=61.2ms
    MotionEvent(deviceId=3, source=0x00005002, action=MOVE, actionButton=0x00000000, flags=0x00000000, metaState=0x00000000, buttonState=0x00000000, edgeFlags=0x00000000, xPrecision=1.0, yPrecision=1.0, displayId=0, pointers=[0: (543.5, 1309.4)]), policyFlags=0x62000000, age=54.7ms
  PendingEvent: <none>
  InboundQueue: <empty>
  ReplacedKeys: <empty>
  Connections:
    0: channelName='WindowManager (server)', windowName='monitor', status=NORMAL, monitor=true, inputPublisherBlocked=false
      OutboundQueue: <empty>
      WaitQueue: <empty>
    5: channelName='72b7776 StatusBar (server)', windowName='Window{72b7776 u0 StatusBar}', status=NORMAL, monitor=false, inputPublisherBlocked=false
      OutboundQueue: <empty>
      WaitQueue: <empty>
    6: channelName='ba2fc6b NavigationBar (server)', windowName='Window{ba2fc6b u0 NavigationBar}', status=NORMAL, monitor=false, inputPublisherBlocked=false
      OutboundQueue: <empty>
      WaitQueue: <empty>
    12: channelName='3c007ad com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher (server)', windowName='Window{3c007ad u0 com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher}', status=NORMAL, monitor=false, inputPublisherBlocked=false
      OutboundQueue: <empty>
      WaitQueue: length=3
        MotionEvent(deviceId=3, source=0x00005002, action=MOVE, actionButton=0x00000000, flags=0x00000000, metaState=0x00000000, buttonState=0x00000000, edgeFlags=0x00000000, xPrecision=1.0, yPrecision=1.0, displayId=0, pointers=[0: (634.4, 1329.4)]), policyFlags=0x62000000, targetFlags=0x00000105, resolvedAction=2, age=17.4ms, wait=16.8ms
        MotionEvent(deviceId=3, source=0x00005002, action=MOVE, actionButton=0x00000000, flags=0x00000000, metaState=0x00000000, buttonState=0x00000000, edgeFlags=0x00000000, xPrecision=1.0, yPrecision=1.0, displayId=0, pointers=[0: (647.4, 1333.4)]), policyFlags=0x62000000, targetFlags=0x00000105, resolvedAction=2, age=11.1ms, wait=10.4ms
        MotionEvent(deviceId=3, source=0x00005002, action=MOVE, actionButton=0x00000000, flags=0x00000000, metaState=0x00000000, buttonState=0x00000000, edgeFlags=0x00000000, xPrecision=1.0, yPrecision=1.0, displayId=0, pointers=[0: (659.4, 1337.4)]), policyFlags=0x62000000, targetFlags=0x00000105, resolvedAction=2, age=5.2ms, wait=4.6ms
  AppSwitch: not pending
  Configuration:
    KeyRepeatDelay: 50.0ms
    KeyRepeatTimeout: 500.0ms
```

## HandlerThread

### BackgroundThread

com/android/internal/os/BackgroundThread.java

```
private BackgroundThread() {
    super("android.bg", android.os.Process.THREAD_PRIORITY_BACKGROUND);
}
```

Systrace 中的 BackgroundThread
[![-w1082](https://androidperformance.com/images/15808252037825.jpg)](https://androidperformance.com/images/15808252037825.jpg)

BackgroundThread 在系统中使用比较多，许多对性能没有要求的任务，一般都会放到 BackgroundThread 中去执行

[![-w654](https://androidperformance.com/images/15808271946061.jpg)](https://androidperformance.com/images/15808271946061.jpg)

## ServiceThread

ServiceThread 继承自 HandlerThread ，下面介绍的几个工作线程都是继承自 ServiceThread ，分别实现不同的功能，根据线程功能不同，其线程优先级也不同：UIThread、IoThread、DisplayThread、AnimationThread、FgThread、SurfaceAnimationThread

每个 Thread 都有自己的 Looper 、Thread 和 MessageQueue，互相不会影响。Android 系统根据功能，会使用不同的 Thread 来完成。

### UiThread

com/android/server/UiThread.java

```
private UiThread() {
    super("android.ui", Process.THREAD_PRIORITY_FOREGROUND, false /*allowIo*/);
}
```

Systrace 中的 UiThread
[![-w1049](https://androidperformance.com/images/15808252975757.jpg)](https://androidperformance.com/images/15808252975757.jpg)

UiThread 被使用的地方如下，具体的功能可以自己去源码里面查看，关键字是 UiThread.get()
[![-w650](https://androidperformance.com/images/15808258949148.jpg)](https://androidperformance.com/images/15808258949148.jpg)

### IoThread

com/android/server/IoThread.java

```
private IoThread() {
    super("android.io", android.os.Process.THREAD_PRIORITY_DEFAULT, true /*allowIo*/);
}
```

IoThread 被使用的地方如下，具体的功能可以自己去源码里面查看，关键字是 IoThread.get()
[![-w654](https://androidperformance.com/images/15808257964346.jpg)](https://androidperformance.com/images/15808257964346.jpg)

### DisplayThread

com/android/server/DisplayThread.javaa

```
private DisplayThread() {
    // DisplayThread runs important stuff, but these are not as important as things running in
    // AnimationThread. Thus, set the priority to one lower.
    super("android.display", Process.THREAD_PRIORITY_DISPLAY + 1, false /*allowIo*/);
}
```

Systrace 中的 DisplayThread
[![-w1108](https://androidperformance.com/images/15808251210767.jpg)](https://androidperformance.com/images/15808251210767.jpg)

[![-w656](https://androidperformance.com/images/15808259701453.jpg)](https://androidperformance.com/images/15808259701453.jpg)

### AnimationThread

com/android/server/AnimationThread.java

```
private AnimationThread() {
    super("android.anim", THREAD_PRIORITY_DISPLAY, false /*allowIo*/);
}
```

Systrace 中的 AnimationThread
[![-w902](https://androidperformance.com/images/15808255124784.jpg)](https://androidperformance.com/images/15808255124784.jpg)

AnimationThread 在源码中的使用，可以看到 WindowAnimator 的动画执行也是在 AnimationThread 线程中的，Android P 增加了一个 SurfaceAnimationThread 来分担 AnimationThread 的部分工作，来提高 WindowAnimation 的动画性能

[![-w657](https://androidperformance.com/images/15808260775808.jpg)](https://androidperformance.com/images/15808260775808.jpg)

### FgThread

com/android/server/FgThread.java

```
private FgThread() {
    super("android.fg", android.os.Process.THREAD_PRIORITY_DEFAULT, true /*allowIo*/);
}
```

Systrace 中的 FgThread
[![-w1018](https://androidperformance.com/images/15808253825450.jpg)](https://androidperformance.com/images/15808253825450.jpg)

FgThread 在源码中的使用，可以自己搜一下，下面是具体的使用的一个例子

```
FgThread.getHandler().post(() -> {
    synchronized (mLock) {
        if (mStartedUsers.get(userIdToLockF) != null) {
            Slog.w(TAG, "User was restarted, skipping key eviction");
            return;
        }
    }
    try {
        mInjector.getStorageManager().lockUserKey(userIdToLockF);
    } catch (RemoteException re) {
        throw re.rethrowAsRuntimeException();
    }
    if (userIdToLockF == userId) {
        for (final KeyEvictedCallback callback : keyEvictedCallbacks) {
            callback.keyEvicted(userId);
        }
    }
});
```

### SurfaceAnimationThread

```
com/android/server/wm/SurfaceAnimationThread.java
private SurfaceAnimationThread() {
    super("android.anim.lf", THREAD_PRIORITY_DISPLAY, false /*allowIo*/);
}
```

Systrace 中的 SurfaceAnimationThread
[![-w1148](https://androidperformance.com/images/15808254715766.jpg)](https://androidperformance.com/images/15808254715766.jpg)

SurfaceAnimationThread 的名字叫 android.anim.lf ， 与 android.anim 有区别，
[![-w657](https://androidperformance.com/images/15808262588087.jpg)](https://androidperformance.com/images/15808262588087.jpg)

这个 Thread 主要是执行窗口动画，用于分担 android.anim 线程的一部分动画工作，减少由于锁导致的窗口动画卡顿问题，具体的内容可以看这篇文章：[Android P——LockFreeAnimation](https://zhuanlan.zhihu.com/p/44864987)

```c++
SurfaceAnimationRunner(@Nullable AnimationFrameCallbackProvider callbackProvider,
        AnimatorFactory animatorFactory, Transaction frameTransaction,
        PowerManagerInternal powerManagerInternal) {
    SurfaceAnimationThread.getHandler().runWithScissors(() -> mChoreographer = getSfInstance(),
            0 /* timeout */);
    mFrameTransaction = frameTransaction;
    mAnimationHandler = new AnimationHandler();
    mAnimationHandler.setProvider(callbackProvider != null
            ? callbackProvider
            : new SfVsyncFrameCallbackProvider(mChoreographer));
    mAnimatorFactory = animatorFactory != null
            ? animatorFactory
            : SfValueAnimator::new;
    mPowerManagerInternal = powerManagerInternal;
}
```



# 主线程运行机制的本质

在讲 Choreographer 之前，我们先理一下 Android 主线程运行的本质，其实就是 Message 的处理过程，我们的各种操作，包括每一帧的渲染操作 ，都是通过 Message 的形式发给主线程的 MessageQueue ，MessageQueue 处理完消息继续等下一个消息，如下图所示

**MethodTrace 图示**

[![img](https://androidperformance.com/images/15717420275540.jpg)](https://androidperformance.com/images/15717420275540.jpg)

**Systrace 图示**

[![img](https://androidperformance.com/images/15717420373518.jpg)](https://androidperformance.com/images/15717420373518.jpg)

## 演进

引入 Vsync 之前的 Android 版本，渲染一帧相关的 Message ，中间是没有间隔的，上一帧绘制完，下一帧的 Message 紧接着就开始被处理。这样的问题就是，帧率不稳定，可能高也可能低，不稳定，如下图

**MethodTrace 图示**

[![img](https://androidperformance.com/images/15717420453069.jpg)](https://androidperformance.com/images/15717420453069.jpg)

**Systrace 图示**

[![img](https://androidperformance.com/images/15717420572997.jpg)](https://androidperformance.com/images/15717420572997.jpg)

可以看到这时候的瓶颈是在 dequeueBuffer, 因为屏幕是有刷新周期的, FB 消耗 Front Buffer 的速度是一定的, 所以 SF 消耗 App Buffer 的速度也是一定的, 所以 App 会卡在 dequeueBuffer 这里,这就会导致 App Buffer 获取不稳定, 很容易就会出现卡顿掉帧的情况.

对于用户来说，稳定的帧率才是好的体验，比如你玩王者荣耀，相比 fps 在 60 和 40 之间频繁变化，用户感觉更好的是稳定在 50 fps 的情况.

所以 Android 的演进中，引入了 **Vsync + TripleBuffer + Choreographer** 的机制，其主要目的就是提供一个稳定的帧率输出机制，让软件层和硬件层可以以共同的频率一起工作。

## 引入 Choreographer

Choreographer 的引入，主要是配合 Vsync ，给上层 App 的渲染提供一个稳定的 Message 处理的时机，也就是 Vsync 到来的时候 ，系统通过对 Vsync 信号周期的调整，来控制每一帧绘制操作的时机. 至于为什么 Vsync 周期选择是 16.6ms (60 fps) ，是因为目前大部分手机的屏幕都是 60Hz 的刷新率，也就是 16.6ms 刷新一次，系统为了配合屏幕的刷新频率，将 Vsync 的周期也设置为 16.6 ms，每隔 16.6 ms ，Vsync 信号到来唤醒 Choreographer 来做 App 的绘制操作 ，如果每个 Vsync 周期应用都能渲染完成，那么应用的 fps 就是 60 ，给用户的感觉就是非常流畅，这就是引入 Choreographer 的主要作用

[![img](https://androidperformance.com/images/15722752299458.jpg)](https://androidperformance.com/images/15722752299458.jpg)

当然目前使用 90Hz 刷新率屏幕的手机越来越多，Vsync 周期从 16.6ms 到了 11.1ms，上图中的操作要在更短的时间内完成，对性能的要求也越来越高，具体可以看[新的流畅体验，90Hz 漫谈](https://www.androidperformance.com/2019/05/15/90hz-on-android/) 这篇文章

# Choreographer 简介

Choreographer 扮演 Android 渲染链路中承上启下的角色

1. **承上**：负责接收和处理 App 的各种更新消息和回调，等到 Vsync 到来的时候统一处理。比如集中处理 Input(主要是 Input 事件的处理) 、Animation(动画相关)、Traversal(包括 measure、layout、draw 等操作) ，判断卡顿掉帧情况，记录 CallBack 耗时等
2. **启下**：负责请求和接收 Vsync 信号。接收 Vsync 事件回调(通过 FrameDisplayEventReceiver.onVsync )；请求 Vsync(FrameDisplayEventReceiver.scheduleVsync)

从上面可以看出来， Choreographer 担任的是一个工具人的角色，他之所以重要，是因为通过 **Choreographer + SurfaceFlinger + Vsync + TripleBuffer** 这一套从上到下的机制，保证了 Android App 可以以一个稳定的帧率运行(20fps、90fps 或者 60fps)，减少帧率波动带来的不适感。

了解 Choreographer 还可以帮助 App 开发者知道程序每一帧运行的基本原理，也可以加深对 **Message、Handler、Looper、MessageQueue、Input、Animation、Measure、Layout、Draw** 的理解 , 很多 **APM** 工具也用到了 **Choreographer( 利用 FrameCallback + FrameInfo )** + **MessageQueue ( 利用 IdleHandler )** + **Looper ( 设置自定义 MessageLogging)** 这些组合拳，深入了解了这些之后，再去做优化，脑子里的思路会更清晰。

另外虽然画图是一个比较好的解释流程的好路子，但是我个人不是很喜欢画图，因为平时 Systrace 和 MethodTrace 用的比较多，Systrace 是按从左到右展示整个系统的运行情况的一个工具(包括 cpu、SurfaceFlinger、SystemServer、App 等关键进程)，使用 **Systrace** 和 **MethodTrace** 也可以很方便地展示关键流程。当你对系统代码比较熟悉的时候，看 Systrace 就可以和手机运行的实际情况对应起来。所以下面的文章除了一些网图之外，其他的我会多以 Systrace 来展示。

## 从 Systrace 的角度来看 Choreogrepher 的工作流程

下图以滑动桌面为例子，我们先看一下从左到右滑动桌面的一个完整的预览图（App 进程），可以看到 Systrace 中从左到右，每一个绿色的帧都表示一帧，表示最终我们可以手机上看到的画面

1. 图中每一个灰色的条和白色的条宽度是一个 Vsync 的时间，也就是 16.6ms
2. 每一帧处理的流程：接收到 Vsync 信号回调-> UI Thread –> RenderThread –> SurfaceFlinger(图中未显示)
3. UI Thread 和 RenderThread 就可以完成 App 一帧的渲染，渲染完的 Buffer 抛给 SurfaceFlinger 去合成，然后我们就可以在屏幕上看到这一帧了
4. 可以看到桌面滑动的每一帧耗时都很短（Ui Thread 耗时 + RenderThread 耗时），但是由于 Vsync 的存在，每一帧都会等到 Vsync 才会去做处理

[![img](https://androidperformance.com/images/15717420793673.jpg)](https://androidperformance.com/images/15717420793673.jpg)

有了上面这个整体的概念，我们将 UI Thread 的每一帧放大来看，看看 Choreogrepher 的位置以及 Choreogrepher 是怎么组织每一帧的

[![img](https://androidperformance.com/images/15717420863795.jpg)](https://androidperformance.com/images/15717420863795.jpg)

## Choreographer 的工作流程

1. Choreographer 初始化
   1. 初始化 FrameHandler ，绑定 Looper
   2. 初始化 FrameDisplayEventReceiver ，与 SurfaceFlinger 建立通信用于接收和请求 Vsync
   3. 初始化 CallBackQueues
2. SurfaceFlinger 的 appEventThread 唤醒发送 Vsync ，Choreographer 回调 FrameDisplayEventReceiver.onVsync , 进入 Choreographer 的主处理函数 doFrame
3. Choreographer.doFrame 计算掉帧逻辑
4. Choreographer.doFrame 处理 Choreographer 的第一个 callback ： input
5. Choreographer.doFrame 处理 Choreographer 的第二个 callback ： animation
6. Choreographer.doFrame 处理 Choreographer 的第三个 callback ： insets animation
7. Choreographer.doFrame 处理 Choreographer 的第四个 callback ： traversal
   1. traversal-draw 中 UIThread 与 RenderThread 同步数据
8. Choreographer.doFrame 处理 Choreographer 的第五个 callback ： commit ?
9. RenderThread 处理绘制命令，将处理好的绘制命令发给 GPU 处理
10. 调用 swapBuffer 提交给 SurfaceFlinger 进行合成（此时 Buffer 并没有真正完成，需要等 CPU 完成后 SurfaceFlinger 才能真正使用，新版本的 Systrace 中有 gpu 的 fence 来标识这个时间）

**第一步初始化完成后，后续就会在步骤 2-9 之间循环**

同时也附上这一帧所对应的 MethodTrace（这里预览一下即可，下面会有详细的大图）

[![img](https://androidperformance.com/images/15717420948412.jpg)](https://androidperformance.com/images/15717420948412.jpg)

下面我们就从源码的角度，来看一下具体的实现

## 源码解析

下面从源码的角度来简单看一下，源码只摘抄了部分重要的逻辑，其他的逻辑则被剔除，另外 Native 部分与 SurfaceFlinger 交互的部分也没有列入，不是本文的重点，有兴趣的可以自己去跟一下。

### Choreographer 的初始化

#### Choreographer 的单例初始化

```
// Thread local storage for the choreographer.
private static final ThreadLocal<Choreographer> sThreadInstance =
        new ThreadLocal<Choreographer>() {
    @Override
    protected Choreographer initialValue() {
        // 获取当前线程的 Looper
        Looper looper = Looper.myLooper();
        ......
        // 构造 Choreographer 对象
        Choreographer choreographer = new Choreographer(looper, VSYNC_SOURCE_APP);
        if (looper == Looper.getMainLooper()) {
            mMainInstance = choreographer;
        }
        return choreographer;
    }
};
```

#### Choreographer 的构造函数

```
private Choreographer(Looper looper, int vsyncSource) {
    mLooper = looper;
    // 1. 初始化 FrameHandler
    mHandler = new FrameHandler(looper);
    // 2. 初始化 DisplayEventReceiver
    mDisplayEventReceiver = USE_VSYNC
            ? new FrameDisplayEventReceiver(looper, vsyncSource)
            : null;
    mLastFrameTimeNanos = Long.MIN_VALUE;
    mFrameIntervalNanos = (long)(1000000000 / getRefreshRate());
    //3. 初始化 CallbacksQueues
    mCallbackQueues = new CallbackQueue[CALLBACK_LAST + 1];
    for (int i = 0; i <= CALLBACK_LAST; i++) {
        mCallbackQueues[i] = new CallbackQueue();
    }
    ......
}
```

#### FrameHandler

```
private final class FrameHandler extends Handler {
    ......
    public void handleMessage(Message msg) {
        switch (msg.what) {
            case MSG_DO_FRAME://开始渲染下一帧的操作
                doFrame(System.nanoTime(), 0);
                break;
            case MSG_DO_SCHEDULE_VSYNC://请求 Vsync 
                doScheduleVsync();
                break;
            case MSG_DO_SCHEDULE_CALLBACK://处理 Callback
                doScheduleCallback(msg.arg1);
                break;
        }
    }
}
```

#### Choreographer 初始化链

在 Activity 启动过程，执行完 onResume 后，会调用 Activity.makeVisible()，然后再调用到 addView()， 层层调用会进入如下方法

```
ActivityThread.handleResumeActivity(IBinder, boolean, boolean, String) (android.app) 
-->WindowManagerImpl.addView(View, LayoutParams) (android.view) 
  -->WindowManagerGlobal.addView(View, LayoutParams, Display, Window) (android.view) 
    -->ViewRootImpl.ViewRootImpl(Context, Display) (android.view) 
    public ViewRootImpl(Context context, Display display) {
        ......
        mChoreographer = Choreographer.getInstance();
        ......
    }
```

### FrameDisplayEventReceiver 简介

Vsync 的注册、申请、接收都是通过 FrameDisplayEventReceiver 这个类，所以可以先简单介绍一下。 FrameDisplayEventReceiver 继承 DisplayEventReceiver ， 有三个比较重要的方法

1. onVsync – Vsync 信号回调
2. run – 执行 doFrame
3. scheduleVsync – 请求 Vsync 信号

```
private final class FrameDisplayEventReceiver extends DisplayEventReceiver implements Runnable {
    ......
    @Override
    public void onVsync(long timestampNanos, long physicalDisplayId, int frame) {
        ......
        mTimestampNanos = timestampNanos;
        mFrame = frame;
        Message msg = Message.obtain(mHandler, this);
        msg.setAsynchronous(true);
        mHandler.sendMessageAtTime(msg, timestampNanos / TimeUtils.NANOS_PER_MS);
    }
    @Override
    public void run() {
        mHavePendingVsync = false;
        doFrame(mTimestampNanos, mFrame);
    }
    
    public void scheduleVsync() {
        ......  
        nativeScheduleVsync(mReceiverPtr);
        ......
    }
}
```

### Choreographer 中 Vsync 的注册

从下面的函数调用栈可以看到，Choreographer 的内部类 FrameDisplayEventReceiver.onVsync 负责接收 Vsync 回调，通知 UIThread 进行数据处理。

那么 FrameDisplayEventReceiver 是通过什么方式在 Vsync 信号到来的时候回调 onVsync 呢？答案是 FrameDisplayEventReceiver 的初始化的时候，最终通过监听文件句柄的形式，其对应的初始化流程如下

android/view/Choreographer.java

```
private Choreographer(Looper looper, int vsyncSource) {
    mLooper = looper;
    mDisplayEventReceiver = USE_VSYNC
            ? new FrameDisplayEventReceiver(looper, vsyncSource)
            : null;
    ......
}
```

android/view/Choreographer.java

```
public FrameDisplayEventReceiver(Looper looper, int vsyncSource) {
    super(looper, vsyncSource);
}
```

android/view/DisplayEventReceiver.java

```
public DisplayEventReceiver(Looper looper, int vsyncSource) {
    ......
    mMessageQueue = looper.getQueue();
    mReceiverPtr = nativeInit(new WeakReference<DisplayEventReceiver>(this), mMessageQueue,
            vsyncSource);
}
```

nativeInit 后续的代码可以自己跟一下，可以对照这篇文章和源码，由于篇幅比较多，这里就不细写了(https://www.jianshu.com/p/304f56f5d486) ， 后续梳理好这一块的逻辑后，会在另外的文章更新。

简单来说，FrameDisplayEventReceiver 的初始化过程中，通过 BitTube(本质是一个 socket pair)，来传递和请求 Vsync 事件，当 SurfaceFlinger 收到 Vsync 事件之后，通过 appEventThread 将这个事件通过 BitTube 传给 DisplayEventDispatcher ，DisplayEventDispatcher 通过 BitTube 的接收端监听到 Vsync 事件之后，回调 Choreographer.FrameDisplayEventReceiver.onVsync ，触发开始一帧的绘制，如下图

[![img](https://androidperformance.com/images/15717421215251.jpg)](https://androidperformance.com/images/15717421215251.jpg)

### Choreographer 处理一帧的逻辑

Choreographer 处理绘制的逻辑核心在 Choreographer.doFrame 函数中，从下图可以看到，FrameDisplayEventReceiver.onVsync post 了自己，其 run 方法直接调用了 doFrame 开始一帧的逻辑处理

android/view/Choreographer.java

```
public void onVsync(long timestampNanos, long physicalDisplayId, int frame) {
    ......
    mTimestampNanos = timestampNanos;
    mFrame = frame;
    Message msg = Message.obtain(mHandler, this);
    msg.setAsynchronous(true);
    mHandler.sendMessageAtTime(msg, timestampNanos / TimeUtils.NANOS_PER_MS);
}
public void run() {
    mHavePendingVsync = false;
    doFrame(mTimestampNanos, mFrame);
}
```

doFrame 函数主要做下面几件事

1. 计算掉帧逻辑
2. 记录帧绘制信息
3. 执行 CALLBACK_INPUT、CALLBACK_ANIMATION、CALLBACK_INSETS_ANIMATION、CALLBACK_TRAVERSAL、CALLBACK_COMMIT

### 计算掉帧逻辑

```
void doFrame(long frameTimeNanos, int frame) {
    final long startNanos;
    synchronized (mLock) {
        ......
        long intendedFrameTimeNanos = frameTimeNanos;
        startNanos = System.nanoTime();
        final long jitterNanos = startNanos - frameTimeNanos;
        if (jitterNanos >= mFrameIntervalNanos) {
            final long skippedFrames = jitterNanos / mFrameIntervalNanos;
            if (skippedFrames >= SKIPPED_FRAME_WARNING_LIMIT) {
                Log.i(TAG, "Skipped " + skippedFrames + " frames!  "
                        + "The application may be doing too much work on its main thread.");
            }
        }
        ......
    }
    ......
}
```

Choreographer.doFrame 的掉帧检测比较简单，从下图可以看到，Vsync 信号到来的时候会标记一个 start_time ，执行 doFrame 的时候标记一个 end_time ，这两个时间差就是 Vsync 处理时延，也就是掉帧

[![img](https://androidperformance.com/images/15717421364722.jpg)](https://androidperformance.com/images/15717421364722.jpg)

我们以 Systrace 的掉帧的实际情况来看掉帧的计算逻辑

[![img](https://androidperformance.com/images/15717421441350.jpg)](https://androidperformance.com/images/15717421441350.jpg)

这里需要注意的是，这种方法计算的掉帧，是前一帧的掉帧情况，而不是这一帧的掉帧情况，这个计算方法是有缺陷的，会导致有的掉帧没有被计算到

### 记录帧绘制信息

Choreographer 中 FrameInfo 来负责记录帧的绘制信息，doFrame 执行的时候，会把每一个关键节点的绘制时间记录下来，我们使用 dumpsys gfxinfo 就可以看到。当然 Choreographer 只是记录了一部分，剩余的部分在 hwui 那边来记录。

从 FrameInfo 这些标志就可以看出记录的内容，后面我们看 dumpsys gfxinfo 的时候数据就是按照这个来排列的

```
// Various flags set to provide extra metadata about the current frame
private static final int FLAGS = 0;

// Is this the first-draw following a window layout?
public static final long FLAG_WINDOW_LAYOUT_CHANGED = 1;

// A renderer associated with just a Surface, not with a ViewRootImpl instance.
public static final long FLAG_SURFACE_CANVAS = 1 << 2;

@LongDef(flag = true, value = {
        FLAG_WINDOW_LAYOUT_CHANGED, FLAG_SURFACE_CANVAS })
@Retention(RetentionPolicy.SOURCE)
public @interface FrameInfoFlags {}

// The intended vsync time, unadjusted by jitter
private static final int INTENDED_VSYNC = 1;

// Jitter-adjusted vsync time, this is what was used as input into the
// animation & drawing system
private static final int VSYNC = 2;

// The time of the oldest input event
private static final int OLDEST_INPUT_EVENT = 3;

// The time of the newest input event
private static final int NEWEST_INPUT_EVENT = 4;

// When input event handling started
private static final int HANDLE_INPUT_START = 5;

// When animation evaluations started
private static final int ANIMATION_START = 6;

// When ViewRootImpl#performTraversals() started
private static final int PERFORM_TRAVERSALS_START = 7;

// When View:draw() started
private static final int DRAW_START = 8;
```

doFrame 函数记录从 Vsync time 到 markPerformTraversalsStart 的时间

```
void doFrame(long frameTimeNanos, int frame) {
    ......
    mFrameInfo.setVsync(intendedFrameTimeNanos, frameTimeNanos);
    // 处理 CALLBACK_INPUT Callbacks 
    mFrameInfo.markInputHandlingStart();
    // 处理 CALLBACK_ANIMATION Callbacks
    mFrameInfo.markAnimationsStart();
    // 处理 CALLBACK_INSETS_ANIMATION Callbacks
    // 处理 CALLBACK_TRAVERSAL Callbacks
    mFrameInfo.markPerformTraversalsStart();
    // 处理 CALLBACK_COMMIT Callbacks
    ......
}
```

### 执行 Callbacks

```
void doFrame(long frameTimeNanos, int frame) {
    ......
    // 处理 CALLBACK_INPUT Callbacks 
    doCallbacks(Choreographer.CALLBACK_INPUT, frameTimeNanos);
    // 处理 CALLBACK_ANIMATION Callbacks
    doCallbacks(Choreographer.CALLBACK_ANIMATION, frameTimeNanos);
    // 处理 CALLBACK_INSETS_ANIMATION Callbacks
    doCallbacks(Choreographer.CALLBACK_INSETS_ANIMATION, frameTimeNanos);
    // 处理 CALLBACK_TRAVERSAL Callbacks
    doCallbacks(Choreographer.CALLBACK_TRAVERSAL, frameTimeNanos);
    // 处理 CALLBACK_COMMIT Callbacks
    doCallbacks(Choreographer.CALLBACK_COMMIT, frameTimeNanos);
    ......
}
```

**Input 回调调用栈**

**input callback** 一般是执行 ViewRootImpl.ConsumeBatchedInputRunnable

android/view/ViewRootImpl.java

```
final class ConsumeBatchedInputRunnable implements Runnable {
    @Override
    public void run() {
        doConsumeBatchedInput(mChoreographer.getFrameTimeNanos());
    }
}
void doConsumeBatchedInput(long frameTimeNanos) {
    if (mConsumeBatchedInputScheduled) {
        mConsumeBatchedInputScheduled = false;
        if (mInputEventReceiver != null) {
            if (mInputEventReceiver.consumeBatchedInputEvents(frameTimeNanos)
                    && frameTimeNanos != -1) {
                scheduleConsumeBatchedInput();
            }
        }
        doProcessInputEvents();
    }
}
```

Input 时间经过处理，最终会传给 DecorView 的 dispatchTouchEvent，这就到了我们熟悉的 Input 事件分发

[![img](https://androidperformance.com/images/15717421837064.jpg)](https://androidperformance.com/images/15717421837064.jpg)

**Animation 回调调用栈**

一般我们接触的多的是调用 View.postOnAnimation 的时候，会使用到 CALLBACK_ANIMATION

```
public void postOnAnimation(Runnable action) {
    final AttachInfo attachInfo = mAttachInfo;
    if (attachInfo != null) {
        attachInfo.mViewRootImpl.mChoreographer.postCallback(
                Choreographer.CALLBACK_ANIMATION, action, null);
    } else {
        // Postpone the runnable until we know
        // on which thread it needs to run.
        getRunQueue().post(action);
    }
}
```

那么一般是什么时候回调用到 View.postOnAnimation 呢，我截取了一张图，大家可以自己去看一下，接触最多的应该是 startScroll，Fling 这种操作

[![img](https://androidperformance.com/images/15717421963577.jpg)](https://androidperformance.com/images/15717421963577.jpg)

其调用栈根据其 post 的内容，下面是桌面滑动松手之后的 fling 动画。

[![img](https://androidperformance.com/images/15717422041938.jpg)](https://androidperformance.com/images/15717422041938.jpg)

另外我们的 Choreographer 的 FrameCallback 也是用的 CALLBACK_ANIMATION

```
public void postFrameCallbackDelayed(FrameCallback callback, long delayMillis) {
    if (callback == null) {
        throw new IllegalArgumentException("callback must not be null");
    }

    postCallbackDelayedInternal(CALLBACK_ANIMATION,
            callback, FRAME_CALLBACK_TOKEN, delayMillis);
}
```

**Traversal 调用栈**

```
void scheduleTraversals() {
    if (!mTraversalScheduled) {
        mTraversalScheduled = true;
        //为了提高优先级，先 postSyncBarrier
        mTraversalBarrier = mHandler.getLooper().getQueue().postSyncBarrier();
        mChoreographer.postCallback(
                Choreographer.CALLBACK_TRAVERSAL, mTraversalRunnable, null);
    }
}

final class TraversalRunnable implements Runnable {
    @Override
    public void run() {
        // 真正开始执行 measure、layout、draw
        doTraversal();
    }
}
void doTraversal() {
    if (mTraversalScheduled) {
        mTraversalScheduled = false;
        // 这里把 SyncBarrier remove
mHandler.getLooper().getQueue().removeSyncBarrier(mTraversalBarrier);
        // 真正开始
        performTraversals();
    }
}
private void performTraversals() {
      // measure 操作
      if (focusChangedDueToTouchMode || mWidth != host.getMeasuredWidth() || mHeight != host.getMeasuredHeight() || contentInsetsChanged || updatedConfiguration) {
            performMeasure(childWidthMeasureSpec, childHeightMeasureSpec);
      }
      // layout 操作
      if (didLayout) {
          performLayout(lp, mWidth, mHeight);
      }
      // draw 操作
      if (!cancelDraw && !newSurface) {
          performDraw();
      }
}
```

**doTraversal 的 TraceView 示例**

[![img](https://androidperformance.com/images/15717422180571.jpg)](https://androidperformance.com/images/15717422180571.jpg)

### 下一帧的 Vsync 请求

由于动画、滑动、Fling 这些操作的存在，我们需要一个连续的、稳定的帧率输出机制。这就涉及到了 Vsync 的请求逻辑，在连续的操作，比如动画、滑动、Fling 这些情况下，每一帧的 doFrame 的时候，都会根据情况触发下一个 Vsync 的申请，这样我们就可以获得连续的 Vsync 信号。

看下面的 scheduleTraversals 调用栈(scheduleTraversals 中会触发 Vsync 请求)
[![img](https://androidperformance.com/images/15724225347501.jpg)](https://androidperformance.com/images/15724225347501.jpg)
我们比较熟悉的 invalidate 和 requestLayout 都会触发 Vsync 信号请求

我们下面以 Animation 为例，看看 Animation 是如何驱动下一个 Vsync ，来持续更新画面的

### ObjectAnimator 动画驱动逻辑

android/animation/ObjectAnimator.java

```
public void start() {
    super.start();
}
```

android/animation/ValueAnimator.java

```
private void start(boolean playBackwards) {
    ......
    addAnimationCallback(0); // 动画 start 的时候添加 Animation Callback 
    ......
}
private void addAnimationCallback(long delay) {
    ......
    getAnimationHandler().addAnimationFrameCallback(this, delay);
}
```

android/animation/AnimationHandler.java

```
public void addAnimationFrameCallback(final AnimationFrameCallback callback, long delay) {
    if (mAnimationCallbacks.size() == 0) {
        // post FrameCallback
        getProvider().postFrameCallback(mFrameCallback);
    }
    ......
}

// 这里的 mFrameCallback 回调 doFrame，里面 post了自己
private final Choreographer.FrameCallback mFrameCallback = new Choreographer.FrameCallback() {
    @Override
    public void doFrame(long frameTimeNanos) {
        doAnimationFrame(getProvider().getFrameTime());
        if (mAnimationCallbacks.size() > 0) {
            // post 自己
            getProvider().postFrameCallback(this);
        }
    }
};
```

调用 postFrameCallback 会走到 mChoreographer.postFrameCallback ，这里就会触发 Choreographer 的 Vsync 请求逻辑

android/animation/AnimationHandler.java

```
public void postFrameCallback(Choreographer.FrameCallback callback) {
    mChoreographer.postFrameCallback(callback);
}
```

android/view/Choreographer.java

```
private void postCallbackDelayedInternal(int callbackType,
        Object action, Object token, long delayMillis) {
    synchronized (mLock) {
        final long now = SystemClock.uptimeMillis();
        final long dueTime = now + delayMillis;
        mCallbackQueues[callbackType].addCallbackLocked(dueTime, action, token);

        if (dueTime <= now) {
            // 请求 Vsync scheduleFrameLocked ->scheduleVsyncLocked-> mDisplayEventReceiver.scheduleVsync ->nativeScheduleVsync
            scheduleFrameLocked(now);
        } else {
            Message msg = mHandler.obtainMessage(MSG_DO_SCHEDULE_CALLBACK, action);
            msg.arg1 = callbackType;
            msg.setAsynchronous(true);
            mHandler.sendMessageAtTime(msg, dueTime);
        }
    }
}
```

通过上面的 Animation.start 设置，利用了 Choreographer.FrameCallback 接口，每一帧都去请求下一个 Vsync
**动画过程中一帧的 TraceView 示例**

[![img](https://androidperformance.com/images/15717422327935.jpg)](https://androidperformance.com/images/15717422327935.jpg)

### 源码小结

1. **Choreographer** 是线程单例的，而且必须要和一个 Looper 绑定，因为其内部有一个 Handler 需要和 Looper 绑定，一般是 App 主线程的 Looper 绑定
2. **DisplayEventReceiver** 是一个 abstract class，其 JNI 的代码部分会创建一个IDisplayEventConnection 的 Vsync 监听者对象。这样，来自 AppEventThread 的 VSYNC 中断信号就可以传递给 Choreographer 对象了。当 Vsync 信号到来时，DisplayEventReceiver 的 onVsync 函数将被调用。
3. **DisplayEventReceiver** 还有一个 scheduleVsync 函数。当应用需要绘制UI时，将首先申请一次 Vsync 中断，然后再在中断处理的 onVsync 函数去进行绘制。
4. **Choreographer** 定义了一个 **FrameCallback** **interface**，每当 Vsync 到来时，其 doFrame 函数将被调用。这个接口对 Android Animation 的实现起了很大的帮助作用。以前都是自己控制时间，现在终于有了固定的时间中断。
5. **Choreographer** 的主要功能是，当收到 Vsync 信号时，去调用使用者通过 postCallback 设置的回调函数。目前一共定义了五种类型的回调，它们分别是：
   1. **CALLBACK_INPUT** : 处理输入事件处理有关
   2. **CALLBACK_ANIMATION** ： 处理 Animation 的处理有关
   3. **CALLBACK_INSETS_ANIMATION** ： 处理 Insets Animation 的相关回调
   4. **CALLBACK_TRAVERSAL** : 处理和 UI 等控件绘制有关
   5. **CALLBACK_COMMIT** ： 处理 Commit 相关回调，主要是是用于执行组件 Application/Activity/Service 的 onTrimMemory，在 ApplicationThread 的 scheduleTrimMemory 方法中向 Choreographer 插入的；另外这个 Callback 也提供了一个监测一帧耗时的时机
6. **ListView** 的 Item 初始化(obtain\setup) 会在 input 里面也会在 animation 里面，这取决于
7. **CALLBACK_INPUT** 、**CALLBACK_ANIMATION** 会修改 view 的属性，所以要先与 CALLBACK_TRAVERSAL 执行

## APM 与 Choreographer

由于 Choreographer 的位置，许多性能监控的手段都是利用 Choreographer 来做的，除了自带的掉帧计算，Choreographer 提供的 FrameCallback 和 FrameInfo 都给 App 暴露了接口，让 App 开发者可以通过这些方法监控自身 App 的性能，其中常用的方法如下：

1. 利用 FrameCallback 的 doFrame 回调
2. 利用 FrameInfo 进行监控
   1. 使用 ：adb shell dumpsys gfxinfo framestats
   2. 示例 ：adb shell dumpsys gfxinfo com.meizu.flyme.launcher framestats
3. 利用 SurfaceFlinger 进行监控
   1. 使用 ：adb shell dumpsys SurfaceFlinger –latency
   2. 示例 ：adb shell dumpsys SurfaceFlinger –latency com.meizu.flyme.launcher/com.meizu.flyme.launcher.Launcher#0
4. 利用 SurfaceFlinger PageFlip 机制进行监控
   1. 使用 ： adb service call SurfaceFlinger 1013
   2. 备注：需要系统权限
5. Choreographer 自身的掉帧计算逻辑
6. BlockCanary 基于 Looper 的性能监控

### 利用 FrameCallback 的 doFrame 回调

#### FrameCallback 接口

```
public interface FrameCallback {
    public void doFrame(long frameTimeNanos);
}
```

#### 接口使用

```
Choreographer.getInstance().postFrameCallback(youOwnFrameCallback );
```

#### 接口处理

```
public void postFrameCallbackDelayed(FrameCallback callback, long delayMillis) {
    ......
    postCallbackDelayedInternal(CALLBACK_ANIMATION,
            callback, FRAME_CALLBACK_TOKEN, delayMillis);
}
```

TinyDancer 就是使用了这个方法来计算 FPS (https://github.com/friendlyrobotnyc/TinyDancer)

### 利用 FrameInfo 进行监控

adb shell dumpsys gfxinfo framestats

```
Window: StatusBar
Stats since: 17990256398ns
Total frames rendered: 1562
Janky frames: 361 (23.11%)
50th percentile: 6ms
90th percentile: 23ms
95th percentile: 36ms
99th percentile: 101ms
Number Missed Vsync: 33
Number High input latency: 683
Number Slow UI thread: 273
Number Slow bitmap uploads: 8
Number Slow issue draw commands: 18
Number Frame deadline missed: 287
HISTOGRAM: 5ms=670 6ms=128 7ms=84 8ms=63 9ms=38 10ms=23 11ms=21 12ms=20 13ms=25 14ms=39 15ms=65 16ms=36 17ms=51 18ms=37 19ms=41 20ms=20 21ms=19 22ms=18 23ms=15 24ms=14 25ms=8 26ms=4 27ms=6 28ms=3 29ms=4 30ms=2 31ms=2 32ms=6 34ms=12 36ms=10 38ms=9 40ms=3 42ms=4 44ms=5 46ms=8 48ms=6 53ms=6 57ms=4 61ms=1 65ms=0 69ms=2 73ms=2 77ms=3 81ms=4 85ms=1 89ms=2 93ms=0 97ms=2 101ms=1 105ms=1 109ms=1 113ms=1 117ms=1 121ms=2 125ms=1 129ms=0 133ms=1 150ms=2 200ms=3 250ms=0 300ms=1 350ms=1 400ms=0 450ms=0 500ms=0 550ms=0 600ms=0 650ms=0 

---PROFILEDATA---
Flags,IntendedVsync,Vsync,OldestInputEvent,NewestInputEvent,HandleInputStart,AnimationStart,PerformTraversalsStart,DrawStart,SyncQueued,SyncStart,IssueDrawCommandsStart,SwapBuffers,FrameCompleted,DequeueBufferDuration,QueueBufferDuration,
0,10158314881426,10158314881426,9223372036854775807,0,10158315693363,10158315760759,10158315769821,10158316032165,10158316627842,10158316838988,10158318055915,10158320387269,10158321770654,428000,773000,
0,10158332036261,10158332036261,9223372036854775807,0,10158332799196,10158332868519,10158332877269,10158333137738,10158333780654,10158333993206,10158335078467,10158337689561,10158339307061,474000,885000,
0,10158348665353,10158348665353,9223372036854775807,0,10158349710238,10158349773102,10158349780863,10158350405863,10158351135967,10158351360446,10158352300863,10158354305654,10158355814509,471000,836000,
0,10158365296729,10158365296729,9223372036854775807,0,10158365782373,10158365821019,10158365825238,10158365975290,10158366547946,10158366687217,10158367240706,10158368429248,10158369291852,269000,476000,
```

### 利用 SurfaceFlinger 进行监控

命令解释：

1. 数据的单位是纳秒，时间是以开机时间为起始点
2. 每一次的命令都会得到128行的帧相关的数据

数据：

1. 第一行数据，表示刷新的时间间隔refresh_period
2. 第1列：这一部分的数据表示应用程序绘制图像的时间点
3. 第2列：在SF(软件)将帧提交给H/W(硬件)绘制之前的垂直同步时间，也就是每帧绘制完提交到硬件的时间戳，该列就是垂直同步的时间戳
4. 第3列：在SF将帧提交给H/W的时间点，算是H/W接受完SF发来数据的时间点，绘制完成的时间点。

#### **掉帧 jank 计算**

每一行都可以通过下面的公式得到一个值，该值是一个标准，我们称为jankflag，如果当前行的jankflag与上一行的jankflag发生改变，那么就叫掉帧

ceil((C - A) / refresh-period)

### 利用 SurfaceFlinger PageFlip 机制进行监控

```
Parcel data = Parcel.obtain();
Parcel reply = Parcel.obtain();
                data.writeInterfaceToken("android.ui.ISurfaceComposer");
mFlinger.transact(1013, data, reply, 0);
final int pageFlipCount = reply.readInt();

final long now = System.nanoTime();
final int frames = pageFlipCount - mLastPageFlipCount;
final long duration = now - mLastUpdateTime;
mFps = (float) (frames * 1e9 / duration);
mLastPageFlipCount = pageFlipCount;
mLastUpdateTime = now;
reply.recycle();
data.recycle();
```

### Choreographer 自身的掉帧计算逻辑

SKIPPED_FRAME_WARNING_LIMIT 默认为30 , 由 debug.choreographer.skipwarning 这个属性控制

```
if (jitterNanos >= mFrameIntervalNanos) {
    final long skippedFrames = jitterNanos / mFrameIntervalNanos;
    if (skippedFrames >= SKIPPED_FRAME_WARNING_LIMIT) {
        Log.i(TAG, "Skipped " + skippedFrames + " frames!  "
                + "The application may be doing too much work on its main thread.");
    }
}
```

### BlockCanary

Blockcanary 做性能监控使用的是 Looper 的消息机制，通过对 MessageQueue 中每一个 Message 的前后进行记录，打到监控性能的目的

android/os/Looper.java

```
public static void loop() {
    ...
    for (;;) {
        ...
        // This must be in a local variable, in case a UI event sets the logger
        Printer logging = me.mLogging;
        if (logging != null) {
            logging.println(">>>>> Dispatching to " + msg.target + " " +
                    msg.callback + ": " + msg.what);
        }
        msg.target.dispatchMessage(msg);
        if (logging != null) {
            logging.println("<<<<< Finished to " + msg.target + " " + msg.callback);
        }
        ...
    }
}
```

## MessageQueue 与 Choreographer

所谓的异步消息其实就是这样的，我们可以通过 enqueueBarrier 往消息队列中插入一个 Barrier，那么队列中执行时间在这个 Barrier 以后的同步消息都会被这个 Barrier 拦截住无法执行，直到我们调用 removeBarrier 移除了这个 Barrier，而异步消息则没有影响，消息默认就是同步消息，除非我们调用了 Message 的 setAsynchronous，这个方法是隐藏的。只有在初始化 Handler 时通过参数指定往这个 Handler 发送的消息都是异步的，这样在 Handler 的 enqueueMessage 中就会调用 Message 的 setAsynchronous 设置消息是异步的，从上面 Handler.enqueueMessage 的代码中可以看到。

所谓异步消息，其实只有一个作用，就是在设置 Barrier 时仍可以不受 Barrier 的影响被正常处理，如果没有设置 Barrier，异步消息就与同步消息没有区别，可以通过 removeSyncBarrier 移除 Barrier

**SyncBarrier 在 Choreographer 中使用的一个示例**

scheduleTraversals 的时候 postSyncBarrier

```
void scheduleTraversals() {
    if (!mTraversalScheduled) {
        mTraversalScheduled = true;
        //为了提高优先级，先 postSyncBarrier
        mTraversalBarrier = mHandler.getLooper().getQueue().postSyncBarrier();
        mChoreographer.postCallback(
                Choreographer.CALLBACK_TRAVERSAL, mTraversalRunnable, null);
    }
}
```

doTraversal 的时候 removeSyncBarrier

```
void doTraversal() {
    if (mTraversalScheduled) {
        mTraversalScheduled = false;
        // 这里把 SyncBarrier remove
mHandler.getLooper().getQueue().removeSyncBarrier(mTraversalBarrier);
        // 真正开始
        performTraversals();
    }
}
```

Choreographer post Message 的时候，会把这些消息设为 Asynchronous ，这样 Choreographer 中的这些 Message 的优先级就会比较高，

```
Message msg = mHandler.obtainMessage(MSG_DO_SCHEDULE_CALLBACK, action);
msg.arg1 = callbackType;
msg.setAsynchronous(true);
mHandler.sendMessageAtTime(msg, dueTime);
```

#  MainThread 和 RenderThread 解读

## 正文

这里以滑动列表为例 ，我们截取主线程和渲染线程**一帧**的工作流程(每一帧都会遵循这个流程，不过有的帧需要处理的事情多，有的帧需要处理的事情少) ，重点看 “UI Thread ” 和 RenderThread 这两行

[![img](https://androidperformance.com/images/15732904872967.jpg)](https://androidperformance.com/images/15732904872967.jpg)

**这张图对应的工作流程如下**

1. 主线程处于 Sleep 状态，等待 Vsync 信号
2. Vsync 信号到来，主线程被唤醒，Choreographer 回调 FrameDisplayEventReceiver.onVsync 开始一帧的绘制
3. 处理 App 这一帧的 Input 事件(如果有的话)
4. 处理 App 这一帧的 Animation 事件(如果有的话)
5. 处理 App 这一帧的 Traversal 事件(如果有的话)
6. 主线程与渲染线程同步渲染数据，同步结束后，主线程结束一帧的绘制，可以继续处理下一个 Message(如果有的话，IdleHandler 如果不为空，这时候也会触发处理)，或者进入 Sleep 状态等待下一个 Vsync
7. 渲染线程首先需要从 BufferQueue 里面取一个 Buffer(dequeueBuffer) , 进行数据处理之后，调用 OpenGL 相关的函数，真正地进行渲染操作，然后将这个渲染好的 Buffer 还给 BufferQueue (queueBuffer) , SurfaceFlinger 在 Vsync-SF 到了之后，将所有准备好的 Buffer 取出进行合成(这个流程在讲 SurfaceFlinger 的时候会提到)

上面这个流程在 [Android 基于 Choreographer 的渲染机制详解](https://www.androidperformance.com/2019/10/22/Android-Choreographer/) 这篇文章里面已经介绍的很详细了，包括每一帧的 doFrame 都在做什么、卡顿计算的原理、APM 相关. 没有看过这篇文章的同学，建议先去扫一眼

那么这篇文章我们主要从 [Android 基于 Choreographer 的渲染机制详解](https://www.androidperformance.com/2019/10/22/Android-Choreographer/) 这篇文章没有讲到的几个点来入手，帮你更好地理解主线程和渲染线程

1. 主线程的发展
2. 主线程的创建
3. 渲染线程的创建
4. 主线程和渲染线程的分工
5. 游戏的主线程与渲染线程
6. Flutter 的主线程和渲染线程

## 主线程的创建

Android App 的进程是基于 Linux 的，其管理也是基于 Linux 的进程管理机制，所以其创建也是调用了 fork 函数

frameworks/base/core/jni/com_android_internal_os_Zygote.cpp

```
pid_t pid = fork();
```

Fork 出来的进程，我们这里可以把他看做主线程，但是这个线程还没有和 Android 进行连接，所以无法处理 Android App 的 Message ；由于 Android App 线程运行**基于消息机制** ，那么这个 Fork 出来的主线程需要和 Android 的 Message 消息绑定，才能处理 Android App 的各种 Message

这里就引入了 **ActivityThread** ，确切的说，ActivityThread 应该起名叫 ProcessThread 更贴切一些。ActivityThread 连接了 Fork 出来的进程和 App 的 Message ，他们的通力配合组成了我们熟知的 Android App 主线程。所以说 ActivityThread 其实并不是一个 Thread，而是他初始化了 Message 机制所需要的 MessageQueue、Looper、Handler ，而且其 Handler 负责处理大部分 Message 消息，所以我们习惯上觉得 ActivityThread 是主线程，其实他只是主线程的一个逻辑处理单元。

### ActivityThread 的创建

App 进程 fork 出来之后，回到 App 进程，查找 ActivityThread 的 Main函数

com/android/internal/os/ZygoteInit.java

```
static final Runnable childZygoteInit(
        int targetSdkVersion, String[] argv, ClassLoader classLoader) {
    RuntimeInit.Arguments args = new RuntimeInit.Arguments(argv);
    return RuntimeInit.findStaticMain(args.startClass, args.startArgs, classLoader);
}
```

这里的 startClass 就是 ActivityThread，找到之后调用，逻辑就到了 ActivityThread的main函数

android/app/ActivityThread.java

```
public static void main(String[] args) {
    //1. 初始化 Looper、MessageQueue
    Looper.prepareMainLooper();
    // 2. 初始化 ActivityThread
    ActivityThread thread = new ActivityThread();
    // 3. 主要是调用 AMS.attachApplicationLocked，同步进程信息，做一些初始化工作
    thread.attach(false, startSeq);
    // 4. 获取主线程的 Handler，这里是 H ，基本上 App 的 Message 都会在这个 Handler 里面进行处理 
    if (sMainThreadHandler == null) {
        sMainThreadHandler = thread.getHandler();
    }
    // 5. 初始化完成，Looper 开始工作
    Looper.loop();
}
```

注释里面都很清楚，这里就不详细说了，main 函数处理完成之后，主线程就算是正式上线开始工作，其 Systrace 流程如下：

[![img](https://androidperformance.com/images/15732905074966.jpg)](https://androidperformance.com/images/15732905074966.jpg)

## 渲染线程的创建和发展

主线程讲完了我们来讲渲染线程，渲染线程也就是 RenderThread ，最初的 Android 版本里面是没有渲染线程的，渲染工作都是在主线程完成，使用的也都是 CPU ，调用的是 libSkia 这个库，RenderThread 是在 Android Lollipop 中新加入的组件，负责承担一部分之前主线程的渲染工作，减轻主线程的负担

### 软件绘制

我们一般提到的硬件加速，指的就是 GPU 加速，这里可以理解为用 RenderThread 调用 GPU 来进行渲染加速 。 硬件加速在目前的 Android 中是默认开启的， 所以如果我们什么都不设置，那么我们的进程默认都会有主线程和渲染线程(有可见的内容)。我们如果在 App 的 AndroidManifest 里面，在 Application 标签里面加一个

```
android:hardwareAccelerated="false"
```

我们就可以关闭硬件加速，系统检测到你这个 App 关闭了硬件加速，就不会初始化 RenderThread ，直接 cpu 调用 libSkia 来进行渲染。其 Systrace 的表现如下

[![img](https://androidperformance.com/images/15732905305035.jpg)](https://androidperformance.com/images/15732905305035.jpg)

与这篇文章开头的开了硬件加速的那个图对比，可以看到主线程由于要进行渲染工作，所以执行的时间变长了，也更容易出现卡顿，同时帧与帧直接的空闲间隔也变短了，使得其他 Message 的执行时间被压缩

### 硬件加速绘制

正常情况下，硬件加速是开启的，主线程的 draw 函数并没有真正的执行 drawCall ，而是把要 draw 的内容记录到 DIsplayList 里面，同步到 RenderThread 中，一旦同步完成，主线程就可以被释放出来做其他的事情，RenderThread 则继续进行渲染工作

[![img](https://androidperformance.com/images/15732905407683.jpg)](https://androidperformance.com/images/15732905407683.jpg)

### 渲染线程初始化

渲染线程初始化在真正需要 draw 内容的时候，一般我们启动一个 Activity ，在第一个 draw 执行的时候，会去检测渲染线程是否初始化，如果没有则去进行初始化

android/view/ViewRootImpl.java

```java
mAttachInfo.mThreadedRenderer.initializeIfNeeded(
        mWidth, mHeight, mAttachInfo, mSurface, surfaceInsets);
```

后续直接调用 draw

android/graphics/HardwareRenderer.java

```java
mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);
void draw(View view, AttachInfo attachInfo, DrawCallbacks callbacks) {
    final Choreographer choreographer = attachInfo.mViewRootImpl.mChoreographer;
    choreographer.mFrameInfo.markDrawStart();

    updateRootDisplayList(view, callbacks);

    if (attachInfo.mPendingAnimatingRenderNodes != null) {
        final int count = attachInfo.mPendingAnimatingRenderNodes.size();
        for (int i = 0; i < count; i++) {
            registerAnimatingRenderNode(
                    attachInfo.mPendingAnimatingRenderNodes.get(i));
        }
        attachInfo.mPendingAnimatingRenderNodes.clear();
        attachInfo.mPendingAnimatingRenderNodes = null;
    }

    int syncResult = syncAndDrawFrame(choreographer.mFrameInfo);
    if ((syncResult & SYNC_LOST_SURFACE_REWARD_IF_FOUND) != 0) {
        setEnabled(false);
        attachInfo.mViewRootImpl.mSurface.release();
        attachInfo.mViewRootImpl.invalidate();
    }
    if ((syncResult & SYNC_REDRAW_REQUESTED) != 0) {
        attachInfo.mViewRootImpl.invalidate();
    }
}
```

上面的 draw 只是更新 DIsplayList ，更新结束后，调用 syncAndDrawFrame ，通知渲染线程开始工作，主线程释放。渲染线程的核心实现在 libhwui 库里面，其代码位于 frameworks/base/libs/hwui

frameworks/base/libs/hwui/renderthread/RenderProxy.cpp

```
int RenderProxy::syncAndDrawFrame() {
    return mDrawFrameTask.drawFrame();
}
```

关于 RenderThread 的工作流程这里就不细说了，后续会有专门的篇幅来讲解这个，目前 hwui 这一块的流程也有很多优秀的文章，大家可以对照文章和源码来看，其核心流程在 Systrace 上的表现如下:

[![img](https://androidperformance.com/images/15732905545821.jpg)](https://androidperformance.com/images/15732905545821.jpg)

## 主线程和渲染线程的分工

主线程负责处理进程 Message、处理 Input 事件、处理 Animation 逻辑、处理 Measure、Layout、Draw ，更新 DIsplayList ，但是不涉及 SurfaceFlinger 打交道；渲染线程负责渲染渲染相关的工作，一部分工作也是 CPU 来完成的，一部分操作是调用 OpenGL 函数来完成的

当启动硬件加速后，在 Measure、Layout、Draw 的 Draw 这个环节，Android 使用 DisplayList 进行绘制而非直接使用 CPU 绘制每一帧。DisplayList 是一系列绘制操作的记录，抽象为 RenderNode 类，这样间接的进行绘制操作的优点如下

1. DisplayList 可以按需多次绘制而无须同业务逻辑交互
2. 特定的绘制操作（如 translation， scale 等）可以作用于整个 DisplayList 而无须重新分发绘制操作
3. 当知晓了所有绘制操作后，可以针对其进行优化：例如，所有的文本可以一起进行绘制一次
4. 可以将对 DisplayList 的处理转移至另一个线程（也就是 RenderThread）
5. 主线程在 sync 结束后可以处理其他的 Message，而不用等待 RenderThread 结束

RenderThread 的具体流程大家可以看这篇文章 ： http://www.cocoachina.com/articles/35302

## 游戏的主线程与渲染线程

游戏大多使用单独的渲染线程，有单独的 Surface ，直接跟 SurfaceFlinger 进行交互，其主线程的存在感比较低，绝大部分的逻辑都是自己在自己的渲染线程里面实现的。

大家可以看一下王者荣耀对应的 Systrace ，重点看应用进程和 SurfaceFlinger 进程（30fps）

[![img](https://androidperformance.com/images/15732905635210.jpg)](https://androidperformance.com/images/15732905635210.jpg)

可以看到王者荣耀主线程的主要工作，就是把 Input 事件传给 Unity 的渲染线程，渲染线程收到 Input 事件之后，进行逻辑处理，画面更新等。

[![img](https://androidperformance.com/images/15732905704149.jpg)](https://androidperformance.com/images/15732905704149.jpg)

## Flutter 的主线程和渲染线程

这里提一下 Flutter App 在 Systrace 上的表现，由于 Flutter 的渲染是基于 libSkia 的，所以它也没有 RenderThread ，而是他自建的 RenderEngine ， Flutter 比较重要的两个线程是 ui 线程和 gpu 线程，对应到下面提到的 Framework 和 Engine 两层

[![img](https://androidperformance.com/images/15732905786714.jpg)](https://androidperformance.com/images/15732905786714.jpg)

Flutter 中也会监听 Vsync 信号 ，其 VsyncView 中会以 postFrameCallback 的形式，监听 doFrame 回调，然后调用 nativeOnVsync ，将 Vsync 到来的信息传给 Flutter UI 线程，开始一帧的绘制。

[![img](https://androidperformance.com/images/15732905861662.jpg)](https://androidperformance.com/images/15732905861662.jpg)

可以看到 Flutter 的思路跟游戏开发的思路差不多，不依赖具体的平台，自建渲染管道，更新快，跨平台优势明显。

Flutter SDK 自带 Skia 库，不用等系统升级就可以用到最新的 Skia 库，而且 Google 团队在 Skia 上做了很多优化，所以官方号称性能可以媲美原生应用

[![img](https://androidperformance.com/images/15732905929654.jpg)](https://androidperformance.com/images/15732905929654.jpg)

Flutter 的框架分为 Framework 和 Engine 两层，应用是基于 Framework 层开发的，Framework 负责渲染中的 Build，Layout，Paint，生成 Layer 等环节。Engine 层是 C++实现的渲染引擎，负责把 Framework 生成的 Layer 组合，生成纹理，然后通过 Open GL 接口向 GPU 提交渲染数据。

[![img](https://androidperformance.com/images/15732906008462.jpg)](https://androidperformance.com/images/15732906008462.jpg)

当需要更新 UI 的时候，Framework 通知 Engine，Engine 会等到下个 Vsync 信号到达的时候，会通知 Framework，然后 Framework 会进行 animations, build，layout，compositing，paint，最后生成 layer 提交给 Engine。Engine 会把 layer 进行组合，生成纹理，最后通过 Open Gl 接口提交数据给 GPU，GPU 经过处理后在显示器上面显示。整个流程如下图：

[![img](https://androidperformance.com/images/15732906073036.jpg)](https://androidperformance.com/images/15732906073036.jpg)

## 性能

如果主线程需要处理所有任务，则执行耗时较长的操作（例如，网络访问或数据库查询）将会阻塞整个界面线程。一旦被阻塞，线程将无法分派任何事件，包括绘图事件。主线程执行超时通常会带来两个问题

1. 卡顿：如果主线程 + 渲染线程每一帧的执行都超过 16.6ms(60fps 的情况下)，那么就可能会出现掉帧。
2. 卡死：如果界面线程被阻塞超过几秒钟时间（根据组件不同 , 这里的阈值也不同），用户会看到 “[应用无响应](http://developer.android.google.cn/guide/practices/responsiveness.html)” (ANR) 对话框(部分厂商屏蔽了这个弹框,会直接 Crash 到桌面)

对于用户来说，这两个情况都是用户不愿意看到的，所以对于 App 开发者来说，两个问题是发版本之前必须要解决的，ANR 这个由于有详细的调用栈，所以相对来说比较好定位；但是间歇性卡顿这个，可能就需要使用工具来进行分析了：Systrace + TraceView，所以理解主线程和渲染线程的关系和他们的工作原理是非常重要的，这也是本系列的一个初衷

另外关于卡顿，可以参考下面三篇文章，你的 App 卡顿不一定是你 App 的问题，也有可能是系统的问题，不过不管怎么说，首先要会分析卡顿问题。

1. [Android 中的卡顿丢帧原因概述 - 方法论](https://www.androidperformance.com/2019/09/05/Android-Jank-Debug/)
2. [Android 中的卡顿丢帧原因概述 - 系统篇](https://www.androidperformance.com/2019/09/05/Android-Jank-Due-To-System/)
3. [Android 中的卡顿丢帧原因概述 - 应用篇](https://www.androidperformance.com/2019/09/05/Android-Jank-Due-To-App/)



# Triple Buffer解读

Systrace 中可以看到应用的掉帧情况，我们经常看到说主线程超过 16.6 ms 就会掉帧，其实不然，这和我们这一篇文章讲到的 Triple Buffer 和一定的关系，一般来说，Systrace 中我们从 App 端和 SurfaceFlinger 端一起来判断掉帧情况

## App端判断掉帧

基本上不能从app端判断有没有掉帧，因为BufferQueue和TripleBuffer的存在，此时BufferQueue中可能还有上一帧或者上上帧准备好的Buffer，可以直接被SurfaceFlinger拿去合成，当然也可能没有，如下图不一定掉帧

![img](https://androidperformance.com/images/15764245549172.jpg)

**所以从 Systrace 的 App 端我们是无法直接判断是否掉帧的，需要从 Systrace 里面的 SurfaceFlinger 端去看**

## SurfaceFlinger 端判断掉帧

[![img](https://androidperformance.com/images/15764245828175.jpg)](https://androidperformance.com/images/15764245828175.jpg)

SurfaceFlinger 端可以看到 SurfaceFlinger 主线程和合成情况和应用对应的 BufferQueue 中 Buffer 的情况。如上图，就是一个掉帧的例子。App 没有及时渲染完成，且此时 BufferQueue 中也没有前几帧的 Buffer，所以这一帧 SurfaceFlinger 没有合成对应 App 的 Layer，在用户看来这里就掉了一帧

而在第一张图中我们说从 App 端无法看出是否掉帧，那张图对应的 SurfaceFlinger 的 Trace 如下, 可以看到由于有 Triple Buffer 的存在, SF 这里有之前 App 的 Buffer,所以尽管 App 测一帧超过了 16.6 ms, 但是 SF 这里依然有可用来合成的 Buffer, 所以没有掉帧

[![SurfaceFlinger](https://androidperformance.com/images/15764245923282.jpg)](https://androidperformance.com/images/15764245923282.jpg)

## 逻辑掉帧

上面的掉帧我们是从渲染这边来看的，这种掉帧在 Systrace 中可以很容易就发现；还存在一种掉帧情况叫**逻辑掉帧**

**逻辑掉帧**指的是由于应用自己的代码逻辑问题，导致画面更新的时候，不是以均匀或者物理曲线的方式，而是出现跳跃更新的情况，这种掉帧一般在 Systrace 上没法看出来，但是用户在使用的时候可以明显感觉到

举一个简单的例子，比如说列表滑动的时候，如果我们滑动松手后列表的每一帧前进步长是一个均匀变化的曲线，最后趋近于 0，这样就是完美的；但是如果出现这一帧相比上一帧走了 20，下一帧相比这一帧走了 10，下下一帧相比下一帧走了 30，这种就是跳跃更新，在 Systrace 上每一帧都是及时渲染且 SurfaceFlinger 都及时合成的，但是用户用起来就是觉得会卡. 不过我列举的这个例子中，Android 已经针对这种情况做了优化，感兴趣的可以去看一下 android/view/animation/AnimationUtils.java 这个类，重点看下面三个方法的使用

```java
public static void lockAnimationClock(long vsyncMillis)
public static void unlockAnimationClock()
public static long currentAnimationTimeMillis()
```

Android 系统的动画一般不会有这个问题，但是应用开发者就保不齐会写这种代码，比如做动画的时候根据**当前的时间(而不是 Vsync 到来的时间)**来计算动画属性变化的情况，这种情况下，一旦出现掉帧，动画的变化就会变得不均匀，感兴趣的可以自己思考一下这一块

另外 Android 出现掉帧情况的原因非常多，各位可以参考下面三篇文章食用：

1. [Android 中的卡顿丢帧原因概述 - 方法论](https://www.androidperformance.com/2019/09/05/Android-Jank-Debug/)
2. [Android 中的卡顿丢帧原因概述 - 系统篇](https://www.androidperformance.com/2019/09/05/Android-Jank-Due-To-System/)
3. [Android 中的卡顿丢帧原因概述 - 应用篇](https://www.androidperformance.com/2019/09/05/Android-Jank-Due-To-App/)

## BufferQueue

BufferQueue是一个生产者-消费者模型中的数据结构，一般来说，消费者创建BufferQueue，而生产者一般不和BufferQueue在同一个进程里面

![img](https://androidperformance.com/images/15764246330689.jpg)

其运行逻辑如下

1. 当生产者需要Buffer时，它通过dequeueBuffer并指定Buffer的宽度，高度，像素格式和使用标志，从BufferQueue请求释放Buffer。
2. 生产者将填充缓冲区，并通过调用queueBuffer将缓冲区返回到队列中。
3. 消费者使用acquireBuffer获取Buffer并消费Buffer的内容。
4. 使用完成后，消费者将通过调用releaseBuffer将Buffer返回到队列。

**Android通过Vsync机制来控制Buffer在BufferQueue中的流动时机。**

在 Android App 的渲染流程里面，App 就是个生产者(Producer) ，而 SurfaceFlinger 是一个消费者(Consumer)，所以上面的流程就可以翻译为

1. 当 **App** 需要 Buffer 时，它通过调用 dequeueBuffer（）并指定 Buffer 的宽度，高度，像素格式和使用标志，从 BufferQueue 请求释放 Buffer
2. **App** 可以用 cpu 进行渲染也可以调用用 gpu 来进行渲染，渲染完成后，通过调用 queueBuffer（）将缓冲区返回到 App 对应的 BufferQueue(如果是 gpu 渲染的话，这里还有个 gpu 处理的过程)
3. **SurfaceFlinger** 在收到 Vsync 信号之后，开始准备合成，使用 acquireBuffer（）获取 App 对应的 BufferQueue 中的 Buffer 并进行合成操作
4. 合成结束后，**SurfaceFlinger** 将通过调用 releaseBuffer（）将 Buffer 返回到 App 对应的 BufferQueue

## Single Buffer

单 Buffer 的情况下，因为只有一个 Buffer 可用，那么这个 Buffer 既要用来做合成显示，又要被应用拿去做渲染

[![Single Buffer](https://androidperformance.com/images/15764246600451.jpg)](https://androidperformance.com/images/15764246600451.jpg)

理想情况下，单 Buffer 是可以完成任务的（有 Vsync-Offset 存在的情况下）

1. App 收到 Vsync 信号，获取 Buffer 开始渲染
2. 间隔 Vsync-Offset 时间后，SurfaceFlinger 收到 Vsync 信号，开始合成
3. 屏幕刷新，我们看到合成后的画面

[![Single Buffer](https://androidperformance.com/images/15764246714403.jpg)](https://androidperformance.com/images/15764246714403.jpg)

但是很不幸，理想情况我们也就想一想，这期间如果 App 渲染或者 SurfaceFlinger 合成在屏幕显示刷新之前还没有完成，那么屏幕刷新的时候，拿到的 Buffer 就是不完整的，在用户看来，就有种撕裂的感觉

[![Single Buffer](https://androidperformance.com/images/15764246782401.jpg)](https://androidperformance.com/images/15764246782401.jpg)

当然 Single Buffer 已经没有在使用，上面只是一个例子

## Double Buffer

Double Buffer 相当于 BufferQueue 中有两个 Buffer 可供轮转，消费者在消费 Buffer的同时，生产者也可以拿到备用的 Buffer 进行生产操作

[![Double Buffer](https://androidperformance.com/images/15764246889873.jpg)](https://androidperformance.com/images/15764246889873.jpg)

下面我们来看理想情况下，Double Buffer 的工作流程

[![DoubleBufferPipline_NoJank](https://androidperformance.com/images/DoubleBufferPipline_NoJank.png)](https://androidperformance.com/images/DoubleBufferPipline_NoJank.png)

但是 Double Buffer 也会存在性能上的问题，比如下面的情况，App 连续两帧生产都超过 Vsync 周期(准确的说是错过 SurfaceFlinger 的合成时机) ，就会出现掉帧情况，只有在Vsync时刻，SurfaceFlinger才会去取Buffer进行合成操作，如果错过了这个时间就会导致取不到新的Buffer，只能重复上一帧的画面，导致掉帧。

[![Double Buffer](https://androidperformance.com/images/15764247063129.jpg)](https://androidperformance.com/images/15764247063129.jpg)



## Triple Buffer

Triple Buffer 中，我们又加入了一个 BackBuffer ，这样的话 BufferQueue 里面就有三个 Buffer 可以轮转了，当 FrontBuffer 在被使用的时候，App 有两个空闲的 Buffer 可以拿去生产，就算生产过程中有 GPU 超时，CPU 任然可以拿到新的 Buffer 进行生产(**即 SurfaceFling 消费 FrontBuffer，GPU 使用一个 BackBuffer，CPU使用一个 BackBuffer**)

[![Triple Buffer](https://androidperformance.com/images/15764247163985.jpg)](https://androidperformance.com/images/15764247163985.jpg)

下面就是引入 Triple Buffer 之后，解决了 Double Buffer 中遇到的由于 Buffer 不足引起的掉帧问题

[![TripleBufferPipline_NoJank](https://androidperformance.com/images/TripleBufferPipline_NoJank.png)](https://androidperformance.com/images/TripleBufferPipline_NoJank.png)

这里把两个图放到一起来看，方便大家做对比（一个是 Double Buffer 掉帧两次，一个是使用 Triple Buffer 只掉了一帧）

[![TripleBuffer_VS_DoubleBuffer](https://androidperformance.com/images/TripleBuffer_VS_DoubleBuffer.png)](https://androidperformance.com/images/TripleBuffer_VS_DoubleBuffer.png)

## Triple Buffer 的作用

### 缓解掉帧

从上一节 Double Buffer 和 Triple Buffer 的对比图可以看到，在这种情况下（出现连续主线程超时），三个 Buffer 的轮转有助于缓解掉帧出现的次数（从掉帧两次 -> 只掉帧一次）

所以从第一节如何定义掉帧这里我们就知道，App 主线程超时不一定会导致掉帧，由于 Triple Buffer 的存在，部分 App 端的掉帧(主要是由于 GPU 导致)，到 SurfaceFlinger 这里未必是掉帧，这是看 Systrace 的时候需要注意的一个点

[![缓解掉帧](https://androidperformance.com/images/15764247460509.jpg)](https://androidperformance.com/images/15764247460509.jpg)

### 减少主线程和渲染线程等待时间

**双 Buffer 的轮转**， App 主线程有时候必须要等待 SurfaceFlinger(消费者)释放 Buffer 后，才能获取 Buffer 进行生产，这时候就有个问题，现在大部分手机 SurfaceFlinger 和 App 同时收到 Vsync 信号，如果出现App 主线程等待 SurfaceFlinger(消费者)释放 Buffer ，那么势必会让 App 主线程的执行时间延后，比如下面这张图，可以明显看到：**Buffer B 并不是在 Vsync 信号来的时候开始被消费(因为还在使用)，而是等 Buffer A 被消费后，Buffer B 被释放，App 才能拿到 Buffer B 进行生产，这期间就有一定的延迟，会让主线程可用的时间变短**

[![减少主线程和渲染线程等待时间](https://androidperformance.com/images/15764247531355.jpg)](https://androidperformance.com/images/15764247531355.jpg)

我们来看一下在 Systrace 中的上面这种情况发生的时候的表现

[![减少主线程和渲染线程等待时间](https://androidperformance.com/images/15764247599570.jpg)](https://androidperformance.com/images/15764247599570.jpg)

而 三个 Buffer 轮转的情况下，则基本不会有这种情况的发生，渲染线程一般在 dequeueBuffer 的时候，都可以顺利拿到可用的 Buffer （当然如果 dequeueBuffer 本身耗时那就不是这里的讨论范围了）

### 降低 GPU 和 SurfaceFlinger 瓶颈

这个比较好理解，双 Buffer 的时候，App 生产的 Buffer 必须要及时拿去让 GPU 进行渲染，然后 SurfaceFlinger 才能进行合成，一旦 GPU 超时，就很容易出现 SurfaceFlinger 无法及时合成而导致掉帧

在三个 Buffer 轮转的时候，App 生产的 Buffer 可以及早进入 BufferQueue，让 GPU 去进行渲染（因为不需要等待，就算这里积累了 2 个 Buffer，下下一帧才去合成，这里也会提早进行，而不是在真正使用之前去匆忙让 GPU 去渲染），另外 SurfaceFlinger 本身的负载如果比较大，三个 Buffer 轮转也会有效降低 dequeueBuffer 的等待时间

比如下面两张图，就是对应的 SurfaceFlinger 和 App 的**双 Buffer 掉帧**情况，由于 SurfaceFlinger 本身就比较耗时（特定场景），而 App 的 dequeueBuffer 得不到及时的响应，导致发生了比较严重的掉帧情况。在换成 Triple Buffer 之后，这种情况就基本上没有了

[![img](https://androidperformance.com/images/15764247685189.jpg)](https://androidperformance.com/images/15764247685189.jpg)

[![img](https://androidperformance.com/images/15764247751046.jpg)](https://androidperformance.com/images/15764247751046.jpg)





# SurfaceFlinger解读

## 定义与图像合成的4大部分

1. 大多数应用在屏幕上一次显示三个层：屏幕顶部的状态栏、底部或侧面的导航栏以及应用界面。有些应用会拥有更多或更少的层（例如，默认主屏幕应用有一个单独的壁纸层，而全屏游戏可能会隐藏状态栏）。每个层都可以单独更新。状态栏和导航栏由系统进程渲染，而应用层由应用渲染，两者之间不进行协调。
2. 设备显示会按一定速率刷新，在手机和平板电脑上通常为 60 fps。如果显示内容在刷新期间更新，则会出现撕裂现象；因此，请务必只在周期之间更新内容。在可以安全更新内容时，系统便会收到来自显示设备的信号。由于历史原因，我们将该信号称为 VSYNC 信号。
3. 刷新率可能会随时间而变化，例如，一些移动设备的帧率范围在 58 fps 到 62 fps 之间，具体要视当前条件而定。对于连接了 HDMI 的电视，刷新率在理论上可以下降到 24 Hz 或 48 Hz，以便与视频相匹配。由于每个刷新周期只能更新屏幕一次，因此以 200 fps 的帧率为显示设备提交缓冲区就是一种资源浪费，因为大多数帧会被舍弃掉。SurfaceFlinger 不会在应用每次提交缓冲区时都执行操作，而是在显示设备准备好接收新的缓冲区时才会唤醒。
4. 当 VSYNC 信号到达时，SurfaceFlinger 会遍历它的层列表，以寻找新的缓冲区。如果找到新的缓冲区，它会获取该缓冲区；否则，它会继续使用以前获取的缓冲区。SurfaceFlinger 必须始终显示内容，因此它会保留一个缓冲区。如果在某个层上没有提交缓冲区，则该层会被忽略。
5. SurfaceFlinger 在收集可见层的所有缓冲区之后，便会询问 Hardware Composer 应如何进行合成。

下面是上述流程所对应的流程图， 简单地说， SurfaceFlinger 最主要的功能:**SurfaceFlinger 接受来自多个来源的数据缓冲区，对它们进行合成，然后发送到显示设备。**

[![img](https://androidperformance.com/images/15816781462135.jpg)](https://androidperformance.com/images/15816781462135.jpg)

那么 Systrace 中，我们关注的重点就是上面这幅图对应的部分

1. App 部分
2. BufferQueue 部分
3. SurfaceFlinger 部分
4. HWComposer 部分

这四部分，在 Systrace 中都有可以对应的地方，以时间发生的顺序排序就是 1、2、3、4，下面我们从 Systrace 的这四部分来看整个渲染的流程

## App 部分

关于 App 部分，其实在[Systrace 基础知识 - MainThread 和 RenderThread 解读](https://www.androidperformance.com/2019/11/06/Android-Systrace-MainThread-And-RenderThread/)这篇文章里面已经说得比较清楚了，不清楚的可以去这篇文章里面看，其主要的流程如下图：

[![img](https://androidperformance.com/images/15818258189902.jpg)](https://androidperformance.com/images/15818258189902.jpg)

从 SurfaceFlinger 的角度来看，App 部分主要负责生产 SurfaceFlinger 合成所需要的 Surface。

App 与 SurfaceFlinger 的交互主要集中在三点

1. Vsync 信号的接收和处理
2. RenderThread 的 dequeueBuffer
3. RenderThread 的 queueBuffer

### Vsync 信号的接收和处理

关于这部分内容可以查看[Android 基于 Choreographer 的渲染机制详解](https://www.androidperformance.com/2019/10/22/Android-Choreographer/) 这篇文章，App 和 SurfaceFlinger 的第一个交互点就是 Vsync 信号的请求和接收，如上图中第一条标识，Vsync-App 信号到达，就是指的是 SurfaceFlinger 的 Vsync-App 信号。应用收到这个信号后，开始一帧的渲染准备

[![img](https://androidperformance.com/images/15822547481351.jpg)](https://androidperformance.com/images/15822547481351.jpg)

### RenderThread 的 dequeueBuffer

dequeue 有出队的意思，dequeueBuffer 顾名思义，就是从队列中拿出一个 Buffer，这个队列就是 SurfaceFlinger 中的 BufferQueue。如下图，应用开始渲染前，首先需要通过 Binder 调用从 SurfaceFlinger 的 BufferQueue 中获取一个 Buffer，其流程如下：

**App 端的 Systrace 如下所示**
[![-w1249](https://androidperformance.com/images/15822556410563.jpg)](https://androidperformance.com/images/15822556410563.jpg)

**SurfaceFlinger 端的 Systrace 如下所示**
[![-w826](https://androidperformance.com/images/15822558376614.jpg)](https://androidperformance.com/images/15822558376614.jpg)

### RenderThread 的 queueBuffer

queue 有入队的意思，queueBuffer 顾名思义就是讲 Buffer 放回到 BufferQueue，App 处理完 Buffer 后（写入具体的 drawcall），会把这个 Buffer 通过 eglSwapBuffersWithDamageKHR -> queueBuffer 这个流程，将 Buffer 放回 BufferQueue，其流程如下

**App 端的 Systrace 如下所示**
[![-w1165](https://androidperformance.com/images/15822960954718.jpg)](https://androidperformance.com/images/15822960954718.jpg)

**SurfaceFlinger 端的 Systrace 如下所示**
[![-w1295](https://androidperformance.com/images/15822964913781.jpg)](https://androidperformance.com/images/15822964913781.jpg)

通过上面三部分，大家应该对下图中的流程会有一个比较直观的了解了
[![-w410](https://androidperformance.com/images/15822965692055.jpg)](https://androidperformance.com/images/15822965692055.jpg)

## BufferQueue 部分

BufferQueue 部分其实在[Systrace 基础知识 - Triple Buffer 解读](https://www.androidperformance.com/2019/12/15/Android-Systrace-Triple-Buffer/#BufferQueue) 这里有讲，如下图，结合上面那张图，每个有显示界面的进程对应一个 BufferQueue，使用方创建并拥有 BufferQueue 数据结构，并且可存在于与其生产方不同的进程中，BufferQueue 工作流程如下：

[![img](https://androidperformance.com/images/15823652509728.jpg)](https://androidperformance.com/images/15823652509728.jpg)

上图主要是 dequeue、queue、acquire、release ，在这个例子里面，App 是**生产者**，负责填充显示缓冲区（Buffer）；SurfaceFlinger 是**消费者**，将各个进程的显示缓冲区做合成操作

1. dequeue(生产者发起) ： 当生产者需要缓冲区时，它会通过调用 dequeueBuffer() 从 BufferQueue 请求一个可用的缓冲区，并指定缓冲区的宽度、高度、像素格式和使用标记。
2. queue(生产者发起)：生产者填充缓冲区并通过调用 queueBuffer() 将缓冲区返回到队列。
3. acquire(消费者发起) ：消费者通过 acquireBuffer() 获取该缓冲区并使用该缓冲区的内容
4. release(消费者发起) ：当消费者操作完成后，它会通过调用 releaseBuffer() 将该缓冲区返回到队列

## SurfaceFlinger部分

### 工作流程

我们知道，SurfaceFlinger的主要工作就是合成：

```
当Vsync信号到达时，SurfaceFlinger就会遍历他的层列表，以寻找新的缓冲区。如果找到新的缓冲区，它会获取该缓冲区；否则，它就会继续使用以前获取的缓冲区。SurfaceFlinger必须始终显示内容，因此它会保留一个缓冲区。SurfaceFlinger在收集完可见层的所有缓冲区之后，便会询问Hardware Composer应如何进行合成。
```

其 Systrace 主线程可用看到其主要是在收到 Vsync 信号后开始工作

![-w1296](https://androidperformance.com/images/15822972813466.jpg)



其对应的代码如下,主要是处理两个 Message

1. MessageQueue::INVALIDATE — 主要是执行 handleMessageTransaction 和 handleMessageInvalidate 这两个方法
2. MessageQueue::REFRESH — 主要是执行 handleMessageRefresh 方法

frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp

```c++
void SurfaceFlinger::onMessageReceived(int32_t what) NO_THREAD_SAFETY_ANALYSIS {
    ATRACE_CALL();
    switch (what) {
        case MessageQueue::INVALIDATE: {
            ......
            bool refreshNeeded = handleMessageTransaction();
            refreshNeeded |= handleMessageInvalidate();
            ......
            break;
        }
        case MessageQueue::REFRESH: {
            handleMessageRefresh();
            break;
        }
    }
}

//handleMessageInvalidate 实现如下
bool SurfaceFlinger::handleMessageInvalidate() {
    ATRACE_CALL();
    bool refreshNeeded = handlePageFlip();

    if (mVisibleRegionsDirty) {
        computeLayerBounds();
        if (mTracingEnabled) {
            mTracing.notify("visibleRegionsDirty");
        }
    }

    for (auto& layer : mLayersPendingRefresh) {
        Region visibleReg;
        visibleReg.set(layer->getScreenBounds());
        invalidateLayerStack(layer, visibleReg);
    }
    mLayersPendingRefresh.clear();
    return refreshNeeded;
}

//handleMessageRefresh 实现如下， SurfaceFlinger 的大部分工作都是在handleMessageRefresh 中发起的
void SurfaceFlinger::handleMessageRefresh() {
    ATRACE_CALL();

    mRefreshPending = false;

    const bool repaintEverything = mRepaintEverything.exchange(false);
    preComposition();
    rebuildLayerStacks();
    calculateWorkingSet();
    for (const auto& [token, display] : mDisplays) {
        beginFrame(display);
        prepareFrame(display);
        doDebugFlashRegions(display, repaintEverything);
        doComposition(display, repaintEverything);
    }

    logLayerStats();

    postFrame();
    postComposition();

    mHadClientComposition = false;
    mHadDeviceComposition = false;
    for (const auto& [token, displayDevice] : mDisplays) {
        auto display = displayDevice->getCompositionDisplay();
        const auto displayId = display->getId();
        mHadClientComposition =
                mHadClientComposition || getHwComposer().hasClientComposition(displayId);
        mHadDeviceComposition =
                mHadDeviceComposition || getHwComposer().hasDeviceComposition(displayId);
    }

    mVsyncModulator.onRefreshed(mHadClientComposition);

    mLayersWithQueuedFrames.clear();
}
```

handleMessageRefresh 中按照重要性主要有下面几个功能

1. 准备工作
   1. preComposition();
   2. rebuildLayerStacks();
   3. calculateWorkingSet();
2. 合成工作
   1. begiFrame(display);
   2. prepareFrame(display);
   3. doDebugFlashRegions(display, repaintEverything);
   4. doComposition(display, repaintEverything);
3. 收尾工作
   1. logLayerStats();
   2. postFrame();
   3. postComposition();

由于显示系统有非常庞大的细节，这里就不一一进行讲解了，如果你的工作在这一部分，那么所有的流程都需要熟悉并掌握，如果只是想熟悉流程，那么不需要太深入，知道 SurfaceFlinger 的主要工作逻辑即可

### 掉帧

通常我们通过Systrace判断应用是否掉帧的时候，一般是直接看SurfaceFlinger部分，主要是下面几个步骤。

1. SurfaceFlinger的主线程在每个Vsync-SF的时候有没有进行合成

2. 如果没有进行合成，需要查看没有合成的原因

   （1）因为SurfaceFlinger检查发现没有可用的Buffer而没有进行合成操作？

   （2）因为SurfaceFlinger被其他的工作占用（比如截图、HWC等）？

3. 如果有合成操作，那么需要看对应的App的可用Buffer个数是否正常：App此时可用的Buffer为0，那么看App为何没有及时queueBuffer（这一般就是应用自身的问题了），因为SurfaceFlinger合成操作触发可能是其他进程有可用的Buffer

## HWComposer部分

以下是官方介绍

1. Hardware Composer HAL（HWC）用于确定通过可用硬件来合成缓冲区的最有效方法。作为HAL，其实是特定于设备的，而且通常由显示设备硬件原始设备制造商（OEM）完成

2. 当您考虑使用叠加平面时，很容易发现这种方法的好处，它会在显示硬件（而不是GPU）中合成多个缓冲区。例如有一部普通的安卓手机，其屏幕方向为纵向，状态栏在顶部，导航栏在底部，其他区域显示应用内容。每个层的内容都在单独的缓冲区中。您可以使用以下任一方法处理合成（第二种方法可以显著提高效率）。

   （1）将应用内容渲染暂存到缓冲区中，然后在其上渲染状态栏，再在其上渲染导航栏，最后将暂存缓冲区传送到显示硬件。

   （2）将三个缓冲区全部传送到显示硬件，并指示它从不同的缓冲区读取屏幕不同部分的数据。

3. 显示处理器功能差异很大。叠加层的数量（无论层是否可以旋转或混合）以及对定位和叠加的限制很难通过API表达的。为了适应这些选项，HWC会执行以下计算：

   （1）SurfaceFlinger向HWC提供一个完整的层列表，并询问”您希望如何处理这些层？“

   （2）HWC的响应方式是将每一个层标记为叠加层或GLES合成。

   （3）SurfaceFlinger会处理所有的GLES合成，将输出缓冲区传送到HWC，并让HWC处理其余部分。

4. 当屏幕上的内容没有变化时，叠加平面的效率可能会低于GL合成。当叠加层内容具有透明像素且叠加层混合在一起时，尤其如此。在此类情况下，HWC 可以选择为部分或全部层请求 GLES 合成，并保留合成的缓冲区。如果 SurfaceFlinger 返回来要求合成同一组缓冲区，HWC 可以继续显示先前合成的暂存缓冲区。这可以延长闲置设备的电池续航时间。

5. 运行 Android 4.4 或更高版本的设备通常支持 4 个叠加平面。尝试合成的层数多于叠加层数会导致系统对其中一些层使用 GLES 合成，这意味着应用使用的层数会对能耗和性能产生重大影响。

我们继续接着看 SurfaceFlinger 主线程的部分，对应上面步骤中的第三步，下图可以看到 SurfaceFlinger 与 HWC 的通信部分
[![-w1149](https://androidperformance.com/images/15823673746926.jpg)](https://androidperformance.com/images/15823673746926.jpg)



这也对应了最上面那张图的后面部分
[![-w563](https://androidperformance.com/images/15823674500263.jpg)](https://androidperformance.com/images/15823674500263.jpg)

不过这其中的细节非常多，这里就不详细说了。至于为什么要提 HWC，因为 HWC 不仅是渲染链路上重要的一环，其性能也会影响整机的性能，[Android 中的卡顿丢帧原因概述 - 系统篇](https://www.androidperformance.com/2019/09/05/Android-Jank-Due-To-System/#3-WHC-Service-执行耗时) 这篇文章里面就有列有 HWC 导致的卡顿问题（性能不足，中断信号慢等问题）

想了解更多 HWC 的知识，可以参考这篇文章[Android P 图形显示系统（一）硬件合成HWC2](https://www.jianshu.com/p/824a9ddf68b9),当然，作者的[Android P 图形显示系](https://www.jianshu.com/nb/28304383)这个系列大家可以仔细看一下



# Vsync解读

Vsync信号可以由硬件产生，也可以由软件模拟，目前主流都是通过硬件HWC产生，HWC可以生成Vsync事件，并通过回调将事件发送到SurfaceFlinger，DisSync会将Vsync生成由Choreographer和SurfaceFlinger使用的VSYNC_APP和VSYNC_SF信号。

![img](https://androidperformance.com/images/15751536260871.jpg)

我们知道Choreographer的引入是为了配个Vsync，给上层App的渲染提供一个稳定的Message处理时机，简单来说就是通过对Vsync信号周期的调整，使得帧率尽可能恒定。渲染层（APP）和Vsync打交道的是Choreographer，合成层与Vsync打交道的是SurfaceFlinger。

## Android图形数据流向

Android的图像流，将数据从App绘制到屏幕显示分为了下面几个阶段：

![img](https://androidperformance.com/images/15751536542613.jpg)

1. **App在收到Vsync信号后，在主线程进行measure、layout、draw操作**，这里对应的是Systrace中的**doFrame**操作。
2. **CPU将数据上传给GPU**，这里ARM设备内存一般都是CPU和GPU一起共享的，这里对应Systrace中渲染线程的flush drawing commands操作。
3. **通知GPU进行渲染**，一般来说，真机的GPU渲染不会阻塞，等待GPU渲染结束，就会通知CPU渲染结束，CPU就会返回继续执行其他任务，在这里一般会使用**Fence**机制进行CPU与GPU的同步操作，所以这个过程对应着Systrace中的Fence过程
4. **swapBuffers，并通知SurfaceFlinger图层合成。**这里对应这渲染线程的**eglSwapBuffersWithDamageKHR**操作。
5. **SurfaceFlinger开始合成图层**，如果之前提交的GPU渲染任务没有结束，则等待GPU渲染完成，再合成，合成依然依赖的是GPU，这里对应的是Systrace中的SurfaceFlinger主线程的onMessageReceived操作（包括handleTransaction、handleMessageInvalidate、handleMessageRefresh）。在SurfaceFlinger合成的收获，会将一些合成工作委托给Hardware Composer，从而降低来自OpenGL和GPU负载。

（Fence机制：这个其实就是一个资源锁，就像操作系统的pv操作一样，防止同时读写Buffer）

6. 将最终合成好的数据放到屏幕对应的FrameBuffer中，固定刷新的收获就可以看到啦。



## Systrace中的图像数据流

![img](https://androidperformance.com/images/15751536946754.jpg)

上图主要包含SurfaceFlinger、App、HWC三个进程，下面进一步说明数据的流向

1. 第一个Vsync信号到来，SurfaceFlinger和App同时收到Vsync信号/
2. SurfaceFlinger收到Vsync-SF信号后，开始进行App上一帧的Buffer合成。
3. App收到Vsync-app信号，开始进行这一帧的Buffer渲染（对应上面的1、2、3、4阶段）
4. 第二个Vsync信号到来时，SurfaceFlinger和App同时收到Vsync信号，SurfaceFlinger获取App在**（上图第二步）**第二步中渲染的Buffer，开始合成（对应上面的第五阶段），App收到Vsync-app信号，开始新一帧的buffer渲染

## Vsync Offset

Vsync Offset指的是Vsync-app与Vsync-SF之间存在的间隔，通常在0-16.6ms之间（一帧）

![disp_sync_arch](https://androidperformance.com/images/disp_sync_arch.png)

途中phase-sf和phase-app就是针对于HW-Vsync-0的偏移，这两个的差值就是Vsync-Offset

![img](https://androidperformance.com/images/15751537168911.jpg)

可以通过 Dumpsys SurfaceFlinger 来查看对应的值

**Offset 为 0**：（sf phase - app phase = 0)

```
Sync configuration: [using: EGL_ANDROID_native_fence_sync EGL_KHR_wait_sync]
DispSync configuration: 
          app phase 1000000 ns,              sf phase 1000000 ns 
    early app phase 1000000 ns,        early sf phase 1000000 ns 
 early app gl phase 1000000 ns,     early sf gl phase 1000000 ns 
     present offset 0 ns                      refresh 16666666 ns
```

**Offset 不为 0** (SF phase - app phase = 4 ms)

```
Sync configuration: [using: EGL_ANDROID_native_fence_sync EGL_KHR_wait_sync]

VSYNC configuration:
         app phase:   2000000 ns	         SF phase:   6000000 ns
   early app phase:   2000000 ns	   early SF phase:   6000000 ns
GL early app phase:   2000000 ns	GL early SF phase:   6000000 ns
    present offset:         0 ns	     VSYNC period:  16666666 ns
```

### Offset为0

如下图

![img](C:\Users\zjiang.li\Pictures\Camera Roll\15751537800460.jpg)

我们可以看到，app的渲染线程并不长，很短时间就结束了，但是得等到下一个Vsync-SF到来，SurfaceFlinger才会将刚刚App渲染好的Buffer取出合成。

**Vsync Offset的作用：在上述过程中，我们发现每次渲染完都要等Vsync-SF的信号到来才能进行合成操作，如果SF和App同步，那么每次都在渲染上一帧，响应的操作不能更快的显现出来，如果我们设置好对应的Offset，使得App刚渲染完，SF的信号就到达，那么就能马上进行合成，这样给用户的感觉会更流畅跟手。**

### Offset不为0

下图是一个Offset为4ms的案例

![img](https://androidperformance.com/images/15751537928994.jpg)

### Offset机制的优缺点

Offset并没有一个最优的数值，都是根据使用场景和当前性能而变化，很多情况下不好设置

1. 如果配置时间过短，很可能在APP还没有渲染完，SF就收到信号了，那么时长就变成了Offset+Vsync
2. 如果配置时间过长，那么就没有效果了



## HW_Vsync

这里需要说明的是，不是每次申请 Vsync 都会由硬件产生 Vsync，只有此次请求 vsync 的时间距离上次合成时间大于 500ms，才会通知 hwc，请求 HW_VSYNC

以桌面滑动为例，看 SurfaceFlinger 的进程 Trace 可以看到 HW_VSYNC 的状态

[![img](https://androidperformance.com/images/15751538069738.jpg)](https://androidperformance.com/images/15751538069738.jpg)

后续 App 申请 Vsync 时候，会有两种情况，一种是有 HW_VSYNC 的情况，一种是没有有 HW_VSYNC 的情况

## 不使用HW_VSYNC

[![img](https://androidperformance.com/images/15751538170844.jpg)](https://androidperformance.com/images/15751538170844.jpg)

## 使用 HW_VSYNC

[![img](https://androidperformance.com/images/15751538247774.jpg)](https://androidperformance.com/images/15751538247774.jpg)

HW_VSYNC 主要是利用最近的硬件 VSYNC 来做预测,最少要 3 个,最多是 32 个,实际上要用几个则不一定, DispSync 拿到 6 个 VSYNC 后就会计算出 SW_VSYNC,只要收到的 Present Fence 没有超过误差,硬件 VSYNC 就会关掉,不然会继续接收硬件 VSYNC 计算 SW_VSYNC 的值,直到误差小于 threshold.关于这一块的计算具体过程，可以参考这篇文章： [S](https://juejin.im/post/5dbe658be51d452a45800e76#heading-20) [W-VS](https://juejin.im/post/5dbe658be51d452a45800e76#heading-20) [YN](https://juejin.im/post/5dbe658be51d452a45800e76#heading-20) [C](https://juejin.im/post/5dbe658be51d452a45800e76#heading-20)[ 的生成与传递](https://juejin.im/post/5dbe658be51d452a45800e76#heading-20) ，关于这一块的流程大家也可以参考这篇文章，里面有更细节的内容，这里摘录了他的结论

> SurfaceFlinger 通过实现了 HWC2::ComposerCallback 接口，当 HW-VSYNC 到来的时候，SurfaceFlinger 将会收到回调并且发给 DispSync。DispSync 将会把这些 HW-VSYNC 的时间戳记录下来，当累计了足够的 HW-VSYNC 以后（目前是大于等于 6 个），就开始计算 SW-VSYNC 的偏移 mPeriod。计算出来的 mPeriod 将会用于 DispSyncThread 用来模拟 HW-VSYNC 的周期性起来并且通知对 VSYNC 感兴趣的 Listener，这些 Listener 包括 SurfaceFlinger 和所有需要渲染画面的 app。这些 Listener 通过 EventThread 以 Connection 的抽象形式注册到 EventThread。DispSyncThread 与 EventThread 通过 DispSyncSource 作为中间人进行连接。EventThread 在收到 SW-VSYNC 以后将会把通知所有感兴趣的 Connection，然后 SurfaceFlinger 开始合成，app 开始画帧。在收到足够多的 HW-VSYNC 并且在误差允许的范围内，将会关闭通过 EventControlThread 关闭 HW-VSYNC。



# Binder和锁竞争解读

这里放一张文章里面的 Binder 架构图 ， 本文主要是以 Systrace 为主，所以会讲 Systrace 中的 Binder 表现，不涉及 Binder 的实现

[![img](https://androidperformance.com/images/15756309069397.jpg)](https://androidperformance.com/images/15756309069397.jpg)

## Binder 调用图例

Binder 主要是用来跨进程进行通信，可以看下面这张图，简单显示了在 Systrace 中 ，Binder 通信是如何显示的

[![img](https://androidperformance.com/images/15756309176435.jpg)](https://androidperformance.com/images/15756309176435.jpg)

图中主要是 SystemServer 进程和 高通的 perf 进程通信，Systrace 中右上角 ViewOption 里面勾选 Flow Events 就可以看到 Binder 的信息

[![img](https://androidperformance.com/images/15756309267278.jpg)](https://androidperformance.com/images/15756309267278.jpg)

点击 Binder 可以查看其详细信息，其中有的信息在分析问题的时候可以用到，这里不做过多的描述

[![img](https://androidperformance.com/images/15756309336019.jpg)](https://androidperformance.com/images/15756309336019.jpg)、

对于 Binder，这里主要介绍如何在 Systrace 中查看 Binder **锁信息**和**锁等待**这两个部分，很多卡顿和响应问题的分析，都离不开这两部分信息的解读，不过最后还是要回归代码，找到问题后，要读源码来理顺其代码逻辑，以方便做相应的优化工作

## Systrace 显示的锁的信息

[![img](https://androidperformance.com/images/15756309429683.jpg)](https://androidperformance.com/images/15756309429683.jpg)

**monitor contention with owner Binder:1605_B (4667) at void com.android.server.wm.ActivityTaskManagerService.activityPaused(android.os.IBinder)(ActivityTaskManagerService.java:1733) waiters=2 blocking from android.app.ActivityManager$StackInfo com.android.server.wm.ActivityTaskManagerService.getFocusedStackInfo()(ActivityTaskManagerService.java:2064)**

上面的话分两段来看，以 **blocking** 为分界线　

### 第一段信息解读

**monitor contention with owner Binder:1605_B (4667) at void com.android.server.wm.ActivityTaskManagerService.activityPaused(android.os.IBinder)(ActivityTaskManagerService.java:1733) waiters=2**

**Monitor** 指的是当前锁对象的池，在 Java 中，每个对象都有两个池，锁(monitor)池和等待池：

**锁池**（同步队列 SynchronizedQueue ）：假设线程 A 已经拥有了某个对象(注意:不是类 )的锁，而其它的线程想要调用这个对象的某个 synchronized 方法(或者 synchronized 块)，由于这些线程在进入对象的 synchronized 方法之前必须先获得该对象的锁的拥有权，但是该对象的锁目前正被线程 A 拥有，所以这些线程就进入了该对象的锁池中。

这里用了争夺(contention)这个词，意思是这里由于在和目前对象的锁正被其他对象（Owner）所持有，所以没法得到该对象的锁的拥有权，所以进入该对象的锁池

**Owner** : 指的是当前**拥有**这个对象的锁的对象。这里是 Binder:1605_B，4667 是其线程 ID。

**at** 后面跟的是**拥有**这个对象的锁的对象正在做什么。这里是在执行 void com.android.server.wm.ActivityTaskManagerService.activityPaused 这个方法，其代码位置是 ：ActivityTaskManagerService.java:1733 其对应的代码如下：

com/android/server/wm/ActivityTaskManagerService.java

```
@Override
public final void activityPaused(IBinder token) {
    final long origId = Binder.clearCallingIdentity();
    synchronized (mGlobalLock) { // 1733 是这一行
        ActivityStack stack = ActivityRecord.getStackLocked(token);
        if (stack != null) {
            stack.activityPausedLocked(token, false);
        }
    }
    Binder.restoreCallingIdentity(origId);
}
```

可以看到这里 synchronized (mGlobalLock) ，获取了 mGlobalLock 锁的拥有权，在他释放这个对象的锁之前，任何其他的调用 synchronized (mGlobalLock) 的地方都得在锁池中等待

**waiters** 值得是锁池里面正在等待锁的操作的个数；这里 waiters=2 表示目前锁池里面已经有一个操作在等待这个对象的锁释放了，加上这个的话就是 3 个了

### 第二段信息解读

**blocking from android.app.ActivityManager$StackInfo com.android.server.wm.ActivityTaskManagerService.getFocusedStackInfo()(ActivityTaskManagerService.java:2064)**

第二段信息相对来说简单一些，就是标识了当前被阻塞等锁的方法 ， 这里是 ActivityManager 的 getFocusedStackInfo 被阻塞，其对应的代码

com/android/server/wm/ActivityTaskManagerService.java

```
@Override
public ActivityManager.StackInfo getFocusedStackInfo() throws RemoteException {
    enforceCallerIsRecentsOrHasPermission(MANAGE_ACTIVITY_STACKS, "getStackInfo()");
    long ident = Binder.clearCallingIdentity();
    try {
        synchronized (mGlobalLock) { // 2064 是这一行 
            ActivityStack focusedStack = getTopDisplayFocusedStack();
            if (focusedStack != null) {
                return mRootActivityContainer.getStackInfo(focusedStack.mStackId);
            }
            return null;
        }
    } finally {
        Binder.restoreCallingIdentity(ident);
    }
}
```

可以看到这里也是调用了 synchronized (ActivityManagerService.this) ，从而需要等待获取 ams 对象的锁拥有权

### 总结

上面这段话翻译过来就是

**ActivityTaskManagerService 的 getFocusedStackInfo 方法在执行过程中被阻塞，原因是因为执行同步方法块的时候，没有拿到同步对象的锁的拥有权；需要等待拥有同步对象的锁拥有权的另外一个方法 ActivityTaskManagerService.activityPaused 执行完成后，才能拿到同步对象的锁的拥有权，然后继续执行**

可以对照原文看上面的翻译

**monitor contention with owner Binder:1605_B (4667)
at void com.android.server.wm.ActivityTaskManagerService.activityPaused(android.os.IBinder)(ActivityTaskManagerService.java:1733)
waiters=2
blocking from android.app.ActivityManager$StackInfo com.android.server.wm.ActivityTaskManagerService.getFocusedStackInfo()(ActivityTaskManagerService.java:2064)**

## 新版的锁信息解读

![img](https://pic3.zhimg.com/80/v2-83f67b7cac1a87ba7ccacbfac6f8772a_720w.png)

我标红的那几个位置显示此线程在执行过程中由于锁问题出现了等待情况！我们把鼠标移动到这个色块，然后单击查看下面的提示：

> monitor contention with owner *$#@#$#%$(手工混淆） (27254) waiters=0 blocking from ClassA.functionB(android.content.Context, java.lang.String)(:-1)



提示信息很清楚有木有——本线程与线程ID为 27254 的线程出现了锁争用，被阻塞的函数为`ClassA.functionB` （忽略我的手工混淆 ^_&）。然后我们看看 27254 的线程在干啥：

![img](https://pic2.zhimg.com/80/v2-2d35ac6de299acc65dbd6eb1b49c5699_720w.png)

果然这个线程在调用同一个函数，三下五除二搞定！现在我们知道问题原因，至于如何解决就需要具体问题具体分析了。



再举个栗子，还是上面那种Trace图，我们看第二个monitor contention的情况，其中上面个线程的提示信息是：

> monitor contention with owner NORMAL_THREAD_1 (27274) waiters=1 blocking from boolean ExternalServiceManagerImpl.createExternalService(ServiceDescription)(ExternalServiceManagerImpl.java:55)

从图中看这两个线程调用的是同一个函数，接下来我们看下面那个线程的提示信息：

> monitor contention with owner NORMAL_THREAD_1 (27274) waiters=0 blocking from boolean ExternalServiceManagerImpl.createExternalService(ServiceDescription)(ExternalServiceManagerImpl.java:55)

现在已经很明显了：这两个线程都在等一个线程ID为 27274，线程名字为 NORMAL_THREAD_1的线程；于是我们去看看这个现在在搞什么鬼：

![img](https://pic2.zhimg.com/80/v2-0db5ced82100acb601eee48a73ddee35_720w.png)

纳尼？？分析到这里，线索已经断了——从Systrace上看不到这个线程现在在干什么。我们需要进一步的信息，怎么做？**加更多的信息**。比如，线程池运行的时候把线程名字修改为Runnable的名字；再比如我们已经知道锁住的代码在 `ExternalServiceManagerImpl.java` 第55行，那么我们可以在这里打印堆栈，查看所有的调用者等等。



从上面两个例子可以看到，Systrace对于锁问题的分析是非常有帮助的：可以直观地给出锁和被锁线程的信息，甚至详细到堆栈；但是Systrace也只能帮你到这里了，至于发生锁问题的原因是什么又会导致什么结果往往还需要发挥你自己的聪明才智，继续一步一步进行「假设－验证－分析」才能找到问题的答案——光靠工具是不行的。



## 等锁分析

还是上面那个 Systrace，Binder 信息里面显示 waiters=2，意味着前面还有两个操作在等锁释放，也就是说总共有三个操作都在等待 Binder:1605_B (4667) 释放锁，我们来看一下 Binder:1605_B 的执行情况

[![img](https://androidperformance.com/images/15756309846544.jpg)](https://androidperformance.com/images/15756309846544.jpg)

从上图可以看到，Binder:1605_B 正在执行 activityPaused，中间也有一些其他的 Binder 操作，最终 activityPaused 执行完成后，释放锁

下面我们就把这个逻辑里面的执行顺序理顺，包括两个 **waiters**

### 锁等待

[![img](https://androidperformance.com/images/15756309922668.jpg)](https://androidperformance.com/images/15756309922668.jpg)

上图中可以看到 mGlobalLock 这个对象锁的争夺情况

1. Binder_1605_B 首先开始执行 **activityPaused**，这个方法中是要获取 mGlobalLock 对象锁的，由于此时 mGlobalLock 没有竞争，所以 activityPaused 获取对象锁之后开始执行
2. android.display 线程开始执行 **checkVisibility** 方法，这个方法也是要获取 mGlobalLock 对象锁的，但是此时 Binder_1605_B 的 activityPaused 持有 mGlobalLock 对象锁 ，所以这里 android.display 的 checkVisibility 开始等待，进入 sleep 状态
3. android.anim 线程开始执行 **relayoutWindow** 方法，这个方法也是要获取 mGlobalLock 对象锁的，但是此时 Binder_1605_B 的 activityPaused 持有 mGlobalLock 对象锁 ，所以这里 android.display 的 checkVisibility 开始等待，进入 sleep 状态
4. android.bg 线程开始执行 **getFocusedStackInfo** 方法，这个方法也是要获取 mGlobalLock 对象锁的，但是此时 Binder_1605_B 的 activityPaused 持有 mGlobalLock 对象锁 ，所以这里 android.display 的 checkVisibility 开始等待，进入 sleep 状态

经过上面四步，就形成了 Binder_1605_B 线程在运行，其他三个争夺 mGlobalLock 对象锁失败的线程分别进入 sleep 状态，等待 Binder_1605_B 执行结束后释放 mGlobalLock 对象锁

### 锁释放

[![img](https://androidperformance.com/images/15756310021037.jpg)](https://androidperformance.com/images/15756310021037.jpg)

上图可以看到 mGlobalLock 锁的释放和后续的流程

1. Binder_1605_B 线程的 **activityPaused** 执行结束，mGlobalLock 对象锁释放
2. 第一个进入等待的 android.display 线程开始执行 **checkVisibility** 方法 ，这里从 android.display 线程的唤醒信息可以看到，是被 Binder_1605_B(4667) 唤醒的
3. android.display 线程的 **checkVisibility** 执行结束，mGlobalLock 对象锁释放
4. 第二个进入等待的 android.anim 线程开始执行 **relayoutWindow** 方法 ，这里从 android.anim 线程的唤醒信息可以看到，是被 android.display(1683) 唤醒的
5. android.anim 线程的 **relayoutWindow** 执行结束，mGlobalLock 对象锁释放
6. 第三个进入等待的 android.bg 线程开始执行 **getFocusedStackInfo** 方法 ，这里从 android.bg 线程的唤醒信息可以看到，是被 android.anim(1684) 唤醒的

经过上面 6 步，这一轮由于 mGlobalLock 对象锁引起的等锁现象结束。这里只是一个简单的例子，在实际情况下，SystemServer 中的 BInder 等锁情况会非常严重，经常 waiter 会到达 7 - 10 个，非常恐怖，比如下面这种：

[![img](https://androidperformance.com/images/15756310119592.jpg)](https://androidperformance.com/images/15756310119592.jpg)

这也就可以解释为什么 Android 手机 App 安装多了、用的久了之后，系统就会卡的一个原因；另外重启后也会有短暂的时候出现这种情况

## 相关代码

### Monitor 信息

art/runtime/monitor.cc

```c++
std::string Monitor::PrettyContentionInfo(const std::string& owner_name,
                                          pid_t owner_tid,
                                          ArtMethod* owners_method,
                                          uint32_t owners_dex_pc,
                                          size_t num_waiters) {
  Locks::mutator_lock_->AssertSharedHeld(Thread::Current());
  const char* owners_filename;
  int32_t owners_line_number = 0;
  if (owners_method != nullptr) {
    TranslateLocation(owners_method, owners_dex_pc, &owners_filename, &owners_line_number);
  }
  std::ostringstream oss;
  oss << "monitor contention with owner " << owner_name << " (" << owner_tid << ")";
  if (owners_method != nullptr) {
    oss << " at " << owners_method->PrettyMethod();
    oss << "(" << owners_filename << ":" << owners_line_number << ")";
  }
  oss << " waiters=" << num_waiters;
  return oss.str();
}
```

### Block 信息

art/runtime/monitor.cc

```c++
if (ATRACE_ENABLED()) {
  if (owner_ != nullptr) {  // Did the owner_ give the lock up?
    std::ostringstream oss;
    std::string name;
    owner_->GetThreadName(name);
    oss << PrettyContentionInfo(name,
                                owner_->GetTid(),
                                owners_method,
                                owners_dex_pc,
                                num_waiters);
    // Add info for contending thread.
    uint32_t pc;
    ArtMethod* m = self->GetCurrentMethod(&pc);
    const char* filename;
    int32_t line_number;
    TranslateLocation(m, pc, &filename, &line_number);
    oss << " blocking from "
        << ArtMethod::PrettyMethod(m) << "(" << (filename != nullptr ? filename : "null")
        << ":" << line_number << ")";
    ATRACE_BEGIN(oss.str().c_str());
    started_trace = true;
  }
}
```



# CPU Info解读

下面是高通骁龙 845 手机 Systrace 对应的 Kernel 中的 CPU Info 区域（底下的一些这里不讲，主要是讲 Kernel CPU 信息）

![](C:\Users\zjiang.li\Pictures\Saved Pictures\15769147700353.jpg)

Systrace 中 CPU Info 一般在最上面，里面经常会用到的信息包括：

1. CPU 频率变化情况
2. 任务执行情况
3. 大小核的调度情况
4. CPU Boost 调度情况

总的来说，Systrace 中的 Kernel CPU Info 这里一般是看任务调度信息，查看是否是频率或者调度导致当前任务出现性能问题，举例如下：

1. 某个场景的任务执行比较慢，我们就可以查看是不是这个任务被调度到了小核？
2. 某个场景的任务执行比较慢，当前执行这个任务的 CPU 频率是不是不够？
3. 我的任务比较特殊，比如指纹解锁，能不能把我这个任务放到大核去跑？
4. 我这个场景对 CPU 要求很高，我能不能要求在我这个场景运行的时候，限制 CPU 最低频率？



## 绑核（针对Linux内核）

**绑核**，顾名思义就是把某个任务绑定到某个或者某些核心上，来满足这个任务的性能需求。

1. 任务本身负载比较高，需要在大核心上面才能满足时间要求。
2. 任务本身不想被频繁切换，需要绑定在某一个核心上面。
3. 任务本身不重要，对时间要求不高，可以绑定或者限制在小核心上面运行。

绑核操作一般是由系统来实现的，常用方法如下

### 配置CPUset

CPUset子系统可以限制某一类的任务跑在特定的CPU或者CPU组里面，比如下面，Android中会划分一些默认的CPU组，厂商可以针对不同的CPU架构进行定制，目前的默认划分如下

1. system-background：一些低优先级的任务会被划分到这里，只能跑到小核心里面。
2. foreground：前台进程
3. top-app：目前正在前台和用户交互的进程
4. background：后台进程

每个CPU架构对应的CPUset的配置都不一样，以下是google的默认配置

~~~ 
//官方默认配置
write /dev/CPUset/top-app/CPUs 0-7
write /dev/CPUset/foreground/CPUs 0-7
write /dev/CPUset/foreground/boost/CPUs 4-7
write /dev/CPUset/background/CPUs 0-7
write /dev/CPUset/system-background/CPUs 0-3
// 自己查看
adb shell cat /dev/CPUset/top-app/CPUs
0-7
~~~

对应的，可以在每个 CPUset 组的 tasks 节点下面看有哪些进程和线程是跑在这个组里面的

```
$ adb shell cat /dev/CPUset/top-app/tasks
1687
1689
1690
3559
```

需要注意每个任务跑在哪个组里面，是动态的，并不是一成不变的，有权限的进程就可以改

部分进程也可以在启动的时候就配置好跑到哪个进程里面，下面是 lmkd 的启动配置，writepid /dev/CPUset/system-background/tasks 这一句把自己安排到了 system-background 这个组里面

```
service lmkd /system/bin/lmkd
    class core
    user lmkd
    group lmkd system readproc
    capabilities DAC_OVERRIDE KILL IPC_LOCK SYS_NICE SYS_RESOURCE BLOCK_SUSPEND
    critical
    socket lmkd seqpacket 0660 system system
    writepid /dev/CPUset/system-background/tasks
```

### 配置affinity

中文大意为“亲和力”，其系统调用的taskset，taskset用来查看和设定”CPU亲和力“，其实就是查看或者配置进程和CPU的绑定关系，让某进程在指定的CPU核上运行，这就是“绑核”。

#### taskset 的用法

**显示进程运行的CPU**

```
taskset -p pid
```

注意，此命令返回的是十六进制的，转换成二进制后，每一位对应一个逻辑 CPU，低位是 0 号CPU，依次类推。如果每个位置上是1，表示该进程绑定了该 CPU。例如，0101 就表示进程绑定在了 0 号和 3 号逻辑 CPU 上了

**绑核设定**

```
taskset -pc 3  pid    表示将进程pid绑定到第3个核上
taskset -c 3 command   表示执行 command 命令，并将 command 启动的进程绑定到第3个核上。
```

Android 中也可以使用这个系统调用，把任务绑定到某个核心上运行。部分较老的内核里面不支持 CPUset，就会用 taskset 来设置。

### 调度算法

在Linux的调度算法中修改调度逻辑，也可以让指定的task跑在指定的核上面，部分厂家的核调度优化就是使用的这种方法。



## 锁频

在一些特定场景下，如果让调度器负责拉频率和迁核，会造成一定的延迟，比如一开始跑在小核，后面一级一级往上拉，非常耗时。基于这种情况，一般选择的都是暴力拉核，直接将所有性能拉高。

目前在以下几个场景中可能会选择锁频

1. 应用启动
2. 应用安装
3. 转屏
4. 窗口动画
5. List Fling
6. Game







