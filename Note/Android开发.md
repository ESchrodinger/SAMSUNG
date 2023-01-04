# Activity解读

## Activity生命周期

![image-20220713093102828](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220713093102828.png)

### Activity的生存期

Activity类中定义了7个回调方法，覆盖了Activity生命周期的每一个环节，下面就来一一介绍这7个方法。

**onCreate**()。这个方法你已经看到过很多次了，我们在每个Activity中都重写了这个方法，它会在Activity第一次被创建的时候调用。你应该在这个方法中完成Activity的初始化操作，比如加载布局、绑定事件等。

**onStart**()。这个方法在Activity由不可见变为可见的时候调用。

**onResume**()。这个方法在Activity准备好和用户进行交互的时候调用。此时的Activity一定位于返回栈的栈顶，并且处于运行状态。

**onPause**()。这个方法在系统准备去启动或者恢复另一个Activity的时候调用。我们通常会在这个方法中将一些消耗CPU的资源释放掉，以及保存一些关键数据，但这个方法的执行速度一定要快，不然会影响到新的栈顶Activity的使用。**被暂停，但不是完全看不到**。

**onStop**()。这个方法在Activity完全不可见的时候调用。它和onPause()方法的主要区别在于，如果启动的新Activity是一个对话框式的Activity，那么onPause()方法会得到执行，而onStop()方法并不会执行。**直接停止，当前页面已经不可见了**。

**onDestroy**()。这个方法在Activity被销毁之前调用，之后Activity的状态将变为销毁状态。

**onRestart**()。这个方法在Activity由停止状态变为运行状态之前调用，也就是Activity被重新启动了。



以上7个方法中除了onRestart()方法，其他都是两两相对的，从而又可以将Activity分为以下3种生存期。

**完整生存期**。Activity在onCreate()方法和onDestroy()方法之间所经历的就是完整生存期。一般情况下，一个Activity会在onCreate()方法中完成各种初始化操作，而在onDestroy()方法中完成释放内存的操作。

**可见生存期**。Activity在onStart()方法和onStop()方法之间所经历的就是可见生存期。在可见生存期内，Activity对于用户总是可见的，即便有可能无法和用户进行交互。我们可以通过这两个方法合理地管理那些对用户可见的资源。比如在onStart()方法中对资源进行加载，而在onStop()方法中对资源进行释放，从而保证处于停止状态的Activity不会占用过多内存。

**前台生存期**。Activity在onResume()方法和onPause()方法之间所经历的就是前台生存期。在前台生存期内，Activity总是处于运行状态，此时的Activity是可以和用户进行交互的，我们平时看到和接触最多的就是这个状态下的Activity。

### 活动被回收

当我们由活动1进入活动2时，如果活动1被回收，当按下返回键时还是会显示活动1，但是此时调用的不是onStart, 而是onCreate，而且此时活动1上的数据都会丢失。需要使用方法**onSaveInstanceState()**,能保证在回收之前被调用，这个可以保存原来的信息。

**onSaveInstanceState**()方法会携带一个Bundle类型的参数，Bundle提供了一系列的方法用于保存数据，比如可以使用putString()方法保存字符串，使用putInt()方法保存整型数据，以此类推。每个保存方法需要传入两个参数，第一个参数是键，用于后面从Bundle中取值，第二个参数是真正要保存的内容。

![image-20220713135723222](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220713135723222.png)

数据是已经保存下来了，那么我们应该在哪里进行恢复呢？细心的你也许早就发现，我们一直使用的**onCreate**()方法其实也有一个Bundle类型的参数。这个参数在一般情况下都是null，但是如果在Activity被系统回收之前，你通过**onSaveInstanceState**()方法保存数据，这个参数就会带有之前保存的全部数据，我们只需要再通过相应的取值方法将数据取出即可。
修改**MainActivity的onCreate()**方法，如下所示：

```java
//在onCreate中添加如下
//TAG = "MainActivity",方便logcat
if(saveInstanceState ！= null){
	String tempData = saveInstanceState.getString("data_key");
    Log.d(TAG,tempData);
}
```



## 活动的启动模式

启动模式一共有4种，分别是standard、singleTop、singleTask和singleInstance，可以在AndroidManifest.xml中通过给<activity>标签指定**android:launchMode**属性来选择启动模式。



### standard

这个是Activity默认的启动模式，在standard模式下，每当启动一个新的Activity，它就会在返回栈中入栈，并处于栈顶的位置。对于使用standard模式的Activity，系统不会在乎这个Activity是否已经在返回栈中存在，每次启动都会创建一个该Activity的新实例。

![image-20220714093807342](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220714093807342.png)

### singleTop

当前活动在栈顶的时候就不会继续创建新的实例，当然如果不在栈顶还是会创建的，需要在AndroidManifest.xml中修改相应活动的启动模式，代码来自zjiangApp

```xml
<activity
          android:name=".FirstActivity"
          android:launchMode="singleTop"//就是这里进行启动模式的设置
          android:label="this is FirstActivity">
	<intent-filter>
    	<action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
    </intent-filter>
</activity>

```

![image-20220714095942028](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220714095942028.png)



### singleTask

这个启动方式就是保证在整个运行过程中，只存在一个实例吗，即使不在栈顶也不会创建新的实例

~~~ xml
<activity
	android:name=".FirstActivity"
	android:launchMode="singleTask"
	android:label="This is FirstActivity">
	<intent-filter>
		<action android:name="android.intent.action.MAIN" />
		<category android:name="android.intent.category.LAUNCHER" />
	</intent-filter>
</activity>
~~~

![image-20220714101932574](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220714101932574.png)







### singleInstance

singleInstance模式应该算是4种启动模式中最特殊也最复杂的一个了，你也需要多花点工夫来理解这个模式。不同于以上3种启动模式，指定为singleInstance模式的Activity会启用一个新的返回栈来管理这个Activity（其实如果singleTask模式指定了不同的taskAffinity，也会启动一个新的返回栈）。

那么这样做有什么意义呢？想象以下场景，假设我们的程序中有一个Activity是允许其他程序调用的，如果想实现其他程序和我们的程序可以共享这个Activity的实例，应该如何实现呢？

使用前面3种启动模式肯定是做不到的，因为每个应用程序都会有自己的返回栈，同一个Activity在不同的返回栈中入栈时必然创建了新的实例。而使用singleInstance模式就可以解决这个问题，在这种模式下，会有一个单独的返回栈来管理这个Activity，不管是哪个应用程序来访问这个Activity，都共用同一个返回栈，也就解决了共享Activity实例的问题。

~~~ xml
<activity
	android:name=".SecondActivity"
	android:launchMode="singleInstance"
	android:label="This is SecondActivity">
	<intent-filter>
		<action android:name="android.intent.action.MAIN" />
		<category android:name="android.intent.category.LAUNCHER" />
	</intent-filter>
</activity>
~~~

![image-20220714110513200](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220714110513200.png)

在这里是给second新开了一个新的返回栈，first和third都存在原来的返回栈中，只有当一个返回栈空了，才会返回其他返回栈的值。

## Activity的最佳实践

### 获取当前正在运行的模块是哪一个活动

再创建一个新的类，继承**AppCompatActivity**

~~~ java
public class BaseAcitvity extends AppCompatActivity{
    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        Log.d("BaseActivity",getClass().getSimpleName());
        //这样就能在控制台看到每个活动创建时的名字
    }
}
~~~

### 随时退出程序

有些时候，应用的返回栈中可能会有好几个活动，这个时候点击返回键只能一步步退栈，不能做到直接退出应用，

这个时候就需要一个专门的集合类对所有活动的那个进行管理，新建一个**ActivityCollector**类

~~~ java
public class ActivityCollector{
	public static List<Activity> activities = new ArrayList<>();
	
    public static void addActivity(Activity activity){
		activities.add(activity);
	}
    
    public static void removeActivity(Activity activity){
        activities.remove(activity);
    }
    
    public static void finishAll(){
        for(Activity activity : activities){
            if(!activity.isFinishing()){
                activity.finish();
            }
        }
        activities.clear();
    }
}
~~~

在活动管理器中，我们创建维护了一个List来暂存活动，然后提供了一个addActivity()方法，用于向ArrayList中添加Activity；提供了一个removeActivity()方法，用于从ArrayList中移除Activity；最后提供了一个finishAll()方法，用于将ArrayList中存储的Activity全部销毁。

接着需要修改BaseActivity的代码

~~~ java
public class BaseAcitvity extends AppCompatActivity{
    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        Log.d("BaseActivity",getClass().getSimpleName());
        //这样就能在控制台看到每个活动创建时的名字
        ActivityCollector.addActivity(this);//将当前的活动那个添加到管理器里面 
    }
    
    @Override
    protected void onDestroy(){
        super.onDestroy();
        ActivityCollector.removeActivity(this);
    }
}
~~~

在BaseActivity的onCreate()方法中调用了ActivityCollector的addActivity()方法，表明将当前正在创建的Activity添加到集合里。然后在BaseActivity中重写onDestroy()方法，并调用了ActivityCollector的removeActivity()方法，表明从集合里移除一个马上要销毁的Activity。

从此以后，不管你想在什么地方退出程序，只需要调用ActivityCollector.finishAll()方法就可以了。例如在ThirdActivity界面想通过点击按钮直接退出程序，只需添加一个按钮调用finishAll就可以了。

当然你也可以在销毁所有活动的代码后面再加上杀掉当前进程的代码，保证程序完全退出

~~~ java
Android.os.Process.killProcess(android.os.Process.myPid());		
~~~

这个方法需要活动进程的id，我们只能知道自己的进程id，所以不能杀掉其他程序。

### 启动活动的最佳写法

多个活动之间进行传递的时候需要使用Intent作为数据传递的媒介，如下

~~~ java
Intent intent = new Intent(FirstActivity.this, SecondActivity.class);
intent.putExtra("param1", "data1");
intent.putExtra("param2", "data2");
startActivity(intent);
~~~

这样并没有问题，但是在复杂的开发中往往不能便捷的知道putExtra中的参数代表的具体信息，在应用性能追踪时会给我们造成阻碍，故可以使用以下添加以下方法：

~~~ java
public class SecondActivity extends BaseActivty{
    public static void actionStart(Context context,String data1,String data2){
        Intent intent = new Intent(context,SecondActivity.class);
        intent.putExtra("param1",data1);
        intent.putExtra("param2",data2);
        context.startActivity(intent);
    } 
}
~~~

在活动First中，使用actionStart启动活动second就可以很清晰的知道需要填入哪些参数。可以节省时间，不需要几个活动代码直接来回查看。



# UI设计

安卓开发中的常用控件（TextView，Button）

控件一般都需要几种常用的属性，用id确定唯一标识符，layout_width，layout_height指定控件的长宽，修改对齐方式可以使用gravity，字体大小和颜色使用textSize，textColor进行修改，Button相比于TextView多了一个textAllCaps，因为Button会将text自动大写，可以通过这个进行关闭。

## EditText

允许用户输入输出，还是很常用的

输入id、layout_width、layout_height就可以了

hint代表输入框中的提示文字

输入内容过多的时候如果使用wrap_content就会很难看，一般使用maxLines来解决这个问题。这样editText最多就是两行，如果内容过多就会向上滚动，而不会继续拉伸。

### Button和EditText结合

实现按钮点击后获取EditText的内容

~~~ java
Button buttonGetText = findViewById(R.id.get_text_button);
        editText = findViewById(R.id.edit_text);
        buttonGetText.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String text = editText.getText().toString();
                if (text.length() != 0)
                    Toast.makeText(MainActivity.this, text, Toast.LENGTH_SHORT).show();
                else
                    Toast.makeText(MainActivity.this, "求你输入好吗", Toast.LENGTH_SHORT).show();
            }
        });
~~~

```
设置一个全局变量EditText，然后再点击事件中调用它的数据，最后再提示栏将它显示出来
```

## ImageView

ImageView是用于在界面上展示图片的一个控件，它可以让我们的程序界面变得更加丰富多
彩。学习这个控件需要提前准备好一些图片，你可以自己准备任意的图片，也可以使用随书源
码附带的图片资源（资源下载地址见前言）。图片通常是放在以drawable开头的目录下的，并
且要带上具体的分辨率。现在最主流的手机屏幕分辨率大多是xxhdpi的，所以我们在res目录下
再新建一个drawable-xxhdpi目录，然后将事先准备好的两张图片img_1.png和img_2.png复
制到该目录当中。
接下来修改activity_main.xml，如下所示：

~~~ XML
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:orientation="vertical"
android:layout_width="match_parent"
android:layout_height="match_parent">
...
<ImageView
android:id="@+id/imageView"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:src="@drawable/img_1"
/>
</LinearLayout>
~~~

同时我们也可以通过代码动态更改图片，再活动代码中创建一个点击事件，更改imageView的数据源

先再xml中配置好

```xml
<ImageView
    android:id="@+id/imageView"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:src="@drawable/img1" />

<Button
    android:id="@+id/change_image_button"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="点击更改图片"/>
```

再在活动代码中编辑

```java
//制作点击更改图片按钮
设置全局变量ImageView imageView

//onCreate函数中添加啊
Button changeImage = findViewById(R.id.change_image_button);
imageView = findViewById(R.id.imageView);
changeImage.setOnClickListener(new View.OnClickListener() {
    @Override
    public void onClick(View view) {
        imageView.setImageResource(R.drawable.klee);
    }
});
```

## ProgressBar

这个玩意是个进度条，表示我们的程序正在加载一些数据。它的用法也非常简单，修改activity_main.xml中的代码，如下所示：

~~~ xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:orientation="vertical"
android:layout_width="match_parent"
android:layout_height="match_parent">
...
<ProgressBar
android:id="@+id/progressBar"
android:layout_width="match_parent"
android:layout_height="wrap_content"
/>
</LinearLayout>
~~~

这时你可能会问，旋转的进度条表明我们的程序正在加载数据，那数据总会有加载完的时候吧，如何才能让进度条在数据加载完成时消失呢？这里我们就需要用到一个新的知识点：Android控件的可见属性。

所有的Android控件都具有这个属性，可以通过android:visibility进行指定，可选值有3种：visible、invisible和gone。

visible表示控件是可见的，这个值是默认值，不指定android:visibility时，控件都是可见的。

invisible表示控件不可见，但是它仍然占据着原来的位置和大小，可以理解成控件变成透明状态了。

gone则表示控件不仅不可见，而且不再占用任何屏幕空间。

**我们可以通过代码来设置控件的可见性，使用的是setVisibility()方法，允许传入View.VISIBLE、**
**View.INVISIBLE和View.GONE这3种值。**



```java
//这个是制作一个按钮控制进度条的出现和消失
Button progressBarButton = findViewById(R.id.progressBar_button);
progressBar = (ProgressBar) findViewById(R.id.progressBar);
progressBarButton.setOnClickListener(new View.OnClickListener() {
    @Override
    public void onClick(View view) {
        if (progressBar.getVisibility() == View.GONE)
            progressBar.setVisibility(View.VISIBLE);
        else
            progressBar.setVisibility(View.GONE);
    }
});
```

同时我们很多时候都有更换进度条样式的情况，默认的进度条样式都是圆形的，可以在xml中更改为水平的

```xml
<ProgressBar
    android:id="@+id/progressBar"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    style="@style/Widget.AppCompat.ProgressBar.Horizontal"
    android:max="100"/>
```

```java
//这个是制作一个按钮控制进度条的出现和消失
Button progressBarButton = findViewById(R.id.progressBar_button);
progressBar = findViewById(R.id.progressBar);//在xml中可以更改进度条样式
progressBarButton.setOnClickListener(new View.OnClickListener() {
    @Override
    public void onClick(View view) {
        if (progressBar.getVisibility() == View.GONE)
            progressBar.setVisibility(View.VISIBLE);
        else
            progressBar.setVisibility(View.GONE);

        int progress = progressBar.getProgress();//获得进度
        progress += 10;
        progressBar.setProgress(progress);//点一次加10
    }
```

## AlterDialog

该插件是再当前界面弹出一个对话框，这个对话框是置于所有界面元素之上，能屏蔽掉其他控件的交互能力，一般是用于误删或者退出，下面是我在thirdActivity中“直接退出按钮”做的一个警告框。

~~~ java
Button endApp = findViewById(R.id.endApp);
        endApp.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                //我打算在这做一个提示弹窗
                AlertDialog.Builder dialog = new AlertDialog.Builder(ThirdActivity.this);
                dialog.setTitle("注意，会彻底退出应用");
                dialog.setCancelable(false);
                dialog.setPositiveButton("确认", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialogInterface, int i) {
                        //再点击确认就会彻底退出
                        ActivityCollector.finishAll();
                    }
                });
                dialog.setNegativeButton("取消", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialogInterface, int i) {
                        //点击取消啥也不发生
                    }
                });
                dialog.show();
                 }
        });
~~~

千万要记得添加show()激活这个dialog

## ProgressDialog

这个和上一个很像，但是包含一个进度条，通常用于比较耗时的操作，希望用户耐心等待。

代码和上面差不多。

~~~java
 Button loadingBar = findViewById(R.id.button3);
        loadingBar.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                ProgressDialog progressDialog = new ProgressDialog(ThirdActivity.this);
                progressDialog.setTitle("等个一会嗷");
                progressDialog.setMessage("给我等嗷...");
                progressDialog.setCancelable(true);
                progressDialog.show();


            }
        });
~~~

## 基本布局

![image-20220726151526063](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220726151526063.png)



结构如上，可以进行多层嵌套。



### 线性布局

有垂直和水平两种模式，需要注意的是，当换成水平的时候，就不能将控件的宽度设置为match_parent了，同理在垂直模式的时候也不能将高度设置成match_parent。

有一个 Android: gravity，用于指定文字在控件中的对齐方式，而 Android: layout_gravity 用于指定控件在布局中的对齐方式。

Android：layout_weight 这个属性可以使我们通过比例的方式来控制控件的大小，

~~~ xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:orientation="horizontal"
android:layout_width="match_parent"
android:layout_height="match_parent">
<EditText
android:id="@+id/input_message"
android:layout_width="0dp"
android:layout_height="wrap_content"
android:layout_weight="1"
android:hint="Type something"
/>
<Button
android:id="@+id/send"
android:layout_width="0dp"
android:layout_height="wrap_content"
android:layout_weight="1"
android:text="Send"
/>
</LinearLayout>
~~~

在上述 layout 中，android:layout_width="0dp" 这里不需要担心，反而是一种标准的写法，这个时候控件的宽度就由Android：layout_weight 决定了，这里设置成1，表示 editText 和 button 平分宽度

![image-20220801103053643](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220801103053643.png)

上述操作之所以会平分系统会将线性布局下的所有控件指定的layout_weight值相加得到一个总值，然后每个控件所占大小的比例就是用该控件的layout_weight值除以刚才算出的总值。



### 相对布局

RelativeLayout又称作相对布局，也是一种非常常用的布局。和LinearLayout的排列规则不同，RelativeLayout显得更加随意，它可以通过相对定位的方式让控件出现在布局的任何位置。也正因为如此，RelativeLayout中的属性非常多，不过这些属性都是有规律可循的，其实并不难理解和记忆。

~~~ xml
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:layout_width="match_parent"
android:layout_height="match_parent">
<Button
android:id="@+id/button1"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_alignParentLeft="true"
android:layout_alignParentTop="true"
android:text="Button 1" />
<Button
android:id="@+id/button2"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_alignParentRight="true"
android:layout_alignParentTop="true"
android:text="Button 2" />
<Button
android:id="@+id/button3"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_centerInParent="true"
android:text="Button 3" />
<Button
android:id="@+id/button4"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_alignParentBottom="true"
android:layout_alignParentLeft="true"
android:text="Button 4" />
<Button
android:id="@+id/button5"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_alignParentBottom="true"
android:layout_alignParentRight="true"
android:text="Button 5" />
</RelativeLayout>
~~~

以上代码不需要做过多解释，因为实在是太好理解了。我们让Button 1和父布局的左上角对齐，Button 2和父布局的右上角对齐，Button 3居中显示，Button 4和父布局的左下角对齐，Button 5和父布局的右下角对齐。虽然android:layout_alignParentLeft、android:layout_alignParentTop、android:layout_alignParentRight、
android:layout_alignParentBottom、android:layout_centerInParent这几个属性我们之前都没接触过，可是它们的名字已经完全说明了它们的作用。重新运行程序，效果如图

![image-20220801110654779](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220801110654779.png)

上面提到的这种情况都是针对于父布局进行定位的，当然控件也可以相对于控件进行定位，如下。

~~~ xml
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:layout_width="match_parent"
android:layout_height="match_parent">
<Button
android:id="@+id/button3"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_centerInParent="true"
android:text="Button 3" />
<Button
android:id="@+id/button1"
android:layout_width="wrap_content"
www.blogss.cn
android:layout_height="wrap_content"
android:layout_above="@id/button3"
android:layout_toLeftOf="@id/button3"
android:text="Button 1" />
<Button
android:id="@+id/button2"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_above="@id/button3"
android:layout_toRightOf="@id/button3"
android:text="Button 2" />
<Button
android:id="@+id/button4"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_below="@id/button3"
android:layout_toLeftOf="@id/button3"
android:text="Button 4" />
<Button
android:id="@+id/button5"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_below="@id/button3"
android:layout_toRightOf="@id/button3"
android:text="Button 5" />
</RelativeLayout>
~~~

RelativeLayout中还有另外一组相对于控件进行定位的属性，android:layout_alignLeft表示让一个控件的左边缘和另一个控件的左边缘对齐，android:layout_alignRight表示让一个控件的右边缘和另一个控件的右边缘对齐。此外，还有android:layout_alignTop和android:layout_alignBottom，道理都是一样的。

![image-20220801112001691](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220801112001691.png)



### 帧布局

FrameLayout又称作帧布局，它相比于前面两种布局就简单太多了，因此它的应用场景少了很多。这种布局没有丰富的定位方式，所有的控件都会默认摆放在布局的左上角。当然也可以通过 Android：layout_gravity对摆放位置做调整。

## 自定义布局

我们所用的所有控件都是直接或间接继承自View的，所用的所有布局都是直接或间接继承自ViewGroup的。View是Android中最基本的一种UI组件，它可以在屏幕上绘制一块矩形区域，并能响应这块区域的各种事件，因此，我们使用的各种控件其实就是在View的基础上又添加了各自特有的功能。而ViewGroup则是一种特殊的View，它可以包含很多子View和子ViewGroup，是一个用于放置控件和布局的容器。

接下来我们试着创建一个一个标题栏来作为我们自创的布局

首先在 layout 目录下创建一个 title.xml 作为布局:

代码如下

~~~ xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:layout_width="match_parent"
android:layout_height="wrap_content"
android:background="@drawable/title_bg">
<Button
android:id="@+id/titleBack"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_gravity="center"
android:layout_margin="5dp"
android:background="@drawable/back_bg"
android:text="Back"
android:textColor="#fff" />
<TextView
android:id="@+id/titleText"
android:layout_width="0dp"
android:layout_height="wrap_content"
android:layout_gravity="center"
android:layout_weight="1"
android:gravity="center"
android:text="Title Text"
android:textColor="#fff"
android:textSize="24sp" />
<Button
android:id="@+id/titleEdit"
android:layout_width="wrap_content"
android:layout_height="wrap_content"
android:layout_gravity="center"
android:layout_margin="5dp"
android:background="@drawable/edit_bg"
android:text="Edit"
android:textColor="#fff" />
</LinearLayout>
~~~

其中 android：background 用于为布局或控件指定一个背景，可以使用颜色或这图片进行填充。

在两个Button中我们都使用了android:layout_margin这个属性，它可以指定控件在上下左右方向上的间距。当然也可以使用android:layout_marginLeft或android:layout_marginTop等属性来单独指定控件在某个方向上的间距。

构建好后只需要在对应需要引入布局的 xml 文件中添加以下代码

~~~ xml
<include layout="@layout/title" />
~~~

记得在相应的 onCreate 中将系统自带的标题栏隐藏

![image-20220801140435623](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20220801140435623.png)



## ListView

简单用法就直接使用自带的布局

先在活动的xml中创建好ListView，用来存放ListView

~~~xml
    <ListView
        android:id="@+id/list_view"
        android:layout_width="match_parent"
        android:layout_height="match_parent"/>
~~~

接着新建一个适配器，将数据装到适配器中

~~~java
ArrayAdapter<String> adapter = new ArrayAdapter<>(SecondActivity.this, android.R.layout.simple_list_item_1,data);
ListView listView = findViewById(R.id.list_view);
listView.setAdapter(adapter);
~~~

这里的 data 是 ListView 中子项的数据，` android.R.layout.simple_list_item_1` 是android自带的子项布局，后面我们可以通过自定义布局来更改它。



### 自定义ListView

自定义 ListView 

接下来我创建一个 fruit 类，这个是 list 子项里面装的东西

~~~java
 public class Fruit{

     private String name;
     private int imageID;

     public Fruit(String name,int imageID){
         this.name = name;
         this.imageID = imageID;
     }

     public String getName(){
         return name;
     }

     public int getImageID(){
         return imageID;
     }
 }
~~~

需要自己重写一个适配器

~~~java
public class FruitAdapter extends ArrayAdapter<Fruit>{

    private int resourceID;
    //这个resourceID其实就是等会导入的布局，xml布局都是int数据类型

    public FruitAdapter(Context context, int textViewResourceID, List<Fruit> object){
        super(context,textViewResourceID,object);
        resourceID = textViewResourceID;
    }

    public View getView(int position, View convertView, ViewGroup parent){
        //得到当前的fruit实例，在每一个子项被加载到屏幕里面后就会被调用
        Fruit fruit = getItem(position);
        //使用layoutInflater来为这个子项加载我们传入的布局，把下面这个当成标准写法就行
        View view = LayoutInflater.from(getContext()).inflate(resourceID, parent, false);

        ImageView fruitImage = (ImageView) view.findViewById(R.id.fruit_image);
        TextView fruitName = (TextView) view.findViewById(R.id.fruit_name);

        fruitImage.setImageResource(fruit.getImageID());
        fruitName.setText(fruit.getName());
        return view;

    }
}
~~~
在onCreate函数中添加

~~~java
//这里是使用自定义listview控件
initFruits();
//这个init，就是初始化一个List<Fruit>
FruitAdapter adapter = new FruitAdapter(SecondActivity.this, R.layout.fruit_item, fruitList);
ListView listView = (ListView) findViewById(R.id.list_view);
listView.setAdapter(adapter);
~~~



### 提升 ListView 的运行效率         

之所以说这个 ListView 很难使用，是因为他有很多细节可以优化，因为在 FruitAdapter 的 getView() 方法中，每次都将布局重新加载了一边，所以当 ListView 快速滚动的时候，这就会成为性能的瓶颈。

修改代码，在 getView 方法中改写如下：

~~~java
public View getView(int position,View convertView,ViewGroup parent){
	Fruit fruit = getItem(position);
    View view;
    if(convertView == null){
        view = LayoutInflater.from(getContext()).inflate(resourceID,parent,false);
    }else{
        view = convertView;
    }
    
    ImageView fruitImage = (ImageView) view.findViewById(R.id.fruit_image);
    TextView fruitName = (TextView) view.findViewById(R.id.fruit_name);

    fruitImage.setImageResource(fruit.getImageID());
    fruitName.setText(fruit.getName());
    return view;
}
~~~

现在，我们将判断是否存在 `convertView`，如果存在就会直接使用，而不会继续 `infalte`，极大的提高了运行效率。但是每次使用的时候都需要 ` findviewById` 方法，这里可以使用 ViewHolder 来对这部分性能进行优化。

~~~java
public View getView(int position,View convertView,ViewGroup parent){
	Fruit fruit = getItem(position);
    View view;
    ViewHolder viewHolder;
    
    if(convertView == null){
        view = LayoutInflater.from(getContext()).inflate(resourceID,parent,false);
        viewHolder = new ViewHolder();
        viewHolder.fruitImage = view.findViewById(R.id.fruit_image);
        viewHolder.fruitName = view.findViewById(R.id.fruit_name);
        view.setTag(viewHolder);//将viewHolder存储在View中
    }else{
        view = convertView;
        viewHolder = (ViewHolder) view.getTag();//重新获取 ViewHolder
    }

    viewHolder.fruitImage.setImageResource(fruit.getImageID());
    viewHolder.fruitName.setText(fruit.getName());
    return view;
}

class ViewHolder{v
	ImageView imageView;
    TextView textView;
}
~~~

我们新建了一个内部类 ` ViewHolder` ，用于对控件实例进行缓存。调用` setTag()` 方法将 ViewHolder 对象存储在 View 中。

### ListView 设置点击事件

想要实现这个功能需要在 ` onCreate` 中添加一个点击事件，接下来添加一个通过 ` Toast` 显示水果名字的方法

``` java
ListView listView = findViewById(R.id.list_view);
listView.setOnItemClickListener(new AdapterView.OnItemClickListener(){
    @Override
    public void onItemClick(AdapterView<?> parent,View view,int position,long id){
        Fruit fruit = fruitList.get(position);
        Toast.makeText(SecondActivity.this,fruit.getName(),Toast.LENGTH_SHORT).show();
    }
});
```



## RecyclerView

### RecyclerView的基本用法

和之前我们所学的所有控件不同，RecyclerView属于新增控件，那么怎样才能让新增的控件在所有Android系统版本上都能使用呢？为此，Google将RecyclerView控件定义在了AndroidX当中，我们只需要在项目的build.gradle中添加RecyclerView库的依赖，就能保证在所有Android系统版本上都可以使用RecyclerView控件了。
打开app/build.gradle文件，在dependencies闭包中添加如下内容：

```xml
dependencies {
implementation fileTree(dir: 'libs', include: ['*.jar'])
implementation"org.jetbrains.kotlin:kotlin-stdlib-jdk7:$kotlin_version"
implementation 'androidx.appcompat:appcompat:1.0.2'
implementation 'androidx.core:core-ktx:1.0.2'
implementation 'androidx.constraintlayout:constraintlayout:1.1.3'
implementation 'androidx.recyclerview:recyclerview:1.0.0'
testImplementation 'junit:junit:4.12'
androidTestImplementation 'androidx.test:runner:1.1.1'
androidTestImplementation 'androidx.test.espresso:espresso-core:3.1.1'
}
```

接下来就是修改 activity_main.xml

```xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
android:layout_width="match_parent"
android:layout_height="match_parent">
<androidx.recyclerview.widget.RecyclerView
android:id="@+id/recyclerView"
android:layout_width="match_parent"
android:layout_height="match_parent" />
</LinearLayout>
```



# 广播机制

Android中的广播主要可以分为两种类型：标准广播和有序广播。



## 广播机制简介

- **标准广播（normal broadcasts）**是一种完全异步执行的广播，在广播发出之后，所有的BroadcastReceiver几乎会在同一时刻收到这条广播消息，因此它们之间没有任何先后顺序可言。这种广播的效率会比较高，但同时也意味着它是**无法被截断**的。标准广播的工作流程如图所示。

![image-20221201174155419](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20221201174155419.png)

- **有序广播（ordered broadcasts）**则是一种同步执行的广播，在广播发出之后，同一时刻只会有一个BroadcastReceiver能够收到这条广播消息，当这个BroadcastReceiver中的逻辑执行完毕后，广播才会继续传递。所以此时的BroadcastReceiver是有先后顺序的，优先级高的BroadcastReceiver就可以先收到广播消息，并且前面的BroadcastReceiver还**可以截断**正在传递的广播，这样后面的BroadcastReceiver就无法收到广播消息了。有序广播的工作流程如图所示。

![image-20221201174245588](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20221201174245588.png)



## 接收系统广播

注册广播的方式一般有两种，一种是在代码中注册，一种是在 Android Manifest.xml 中注册，前者被称为动态注册，后者被称为静态注册。

那么如何创建一个BroadcastReceiver呢？其实只需新建一个类，让它继承自 **BroadcastReceiver**，并重写父类的onReceive()方法就行了。这样当有广播到来时，**onReceive**()方法就会得到执行，具体的逻辑就可以在这个方法中处理。

### 动态注册

```java
public class MainActivity extends AppCompatActivity {

    private IntentFilter intentFilter;

    private NetworkChangeReceiver networkChangeReceiver;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //
        intentFilter = new IntentFilter();
        //当网络状态发生变化的时候，系统会发出下面这一条广播
        //也就是说，我们的广播接收器想要接收什么广播，就会在这里添加相应的action
        intentFilter.addAction(("android.net.conn.CONNECTIVITY_CHANGE"));
        networkChangeReceiver = new NetworkChangeReceiver();
        //将广播接收器和过滤器进行注册
        registerReceiver(networkChangeReceiver,intentFilter);
    }

    @Override
    protected void onDestroy(){
        super.onDestroy();
        //动态注册的广播接收器都需要取消注册才行
        unregisterReceiver(networkChangeReceiver);
    }

    //定义了这个类，在网络状态发生变化时，onReceive就会执行，这里只是简单的用来下toast
    class NetworkChangeReceiver extends BroadcastReceiver {
        @Override
        public void onReceive(Context context, Intent intent){
            Toast.makeText(context, "network changes", Toast.LENGTH_SHORT).show();
        }
    }
}

```



如要显示更加精确的信息，譬如网络是否可用，需要将代码修改

```java
 public void onReceive(Context context, Intent intent){
//            Toast.makeText(context, "network changes", Toast.LENGTH_SHORT).show();
            //这个ConnectivityManager是用来专门管理网络连接的
            ConnectivityManager connectivityManager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            //调用getActiveNetworkInfo获得网络信息
            NetworkInfo networkInfo = connectivityManager.getActiveNetworkInfo();
            if (networkInfo != null && networkInfo.isAvailable()){
                Toast.makeText(context, "网络能用", Toast.LENGTH_SHORT).show();
            }
            else{
                Toast.makeText(context, "网络不能用，赶紧给我连", Toast.LENGTH_SHORT).show();
            }

        }
```

> **这里访问网络状态需要声明权限**，需要在AndroidManifest.xml进行修改

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
	package="com.example.broadcasttest">
    
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    ....
</manifest>
```



### 静态注册

动态注册的BroadcastReceiver可以自由地控制注册与注销，在灵活性方面有很大的优势。但是它存在着一个缺点，即必须在程序启动之后才能接收广播，因为注册的逻辑是写在onCreate()方法中的。那么有没有什么办法可以让程序在未启动的情况下也能接收广播呢？这就需要使用静态注册的方式了。

**接下来创建一个静态注册，实现开机自启的功能**

右击com.example.broadcasttest包→New→Other→Broadcast Receiver，

![image-20221206154837044](C:\Users\zjiang.li\AppData\Roaming\Typora\typora-user-images\image-20221206154837044.png)

Exported属性表示是否允许这个BroadcastReceiver接收本程序以外的广播，Enabled属性表示是否启用这个
BroadcastReceiver。勾选这两个属性，点击“Finish”完成创建。

```java
public class BootCompleteReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        // TODO: This method is called when the BroadcastReceiver is receiving
        // an Intent broadcast.
        Toast.makeText(context, "boot complete", Toast.LENGTH_SHORT).show();
        throw new UnsupportedOperationException("Not yet implemented");
    }
}
```

并且，静态的广播接收器一定要在AndroidManifest.xml文件中注册才可以使用。不过由于我们是再as里面创建的，所以as将相关的配置做好了

```xml
 <receiver
            android:name=".BootCompleteReceiver"
            android:enabled="true"
            android:exported="true"></receiver>
```

不过当前的接收器还是不能正常接收信息的，因为并又没有定义需要被接收的广播，需要修改成以下

```xml
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
```

上述是添加权限，下面这是再receiver中添加需要接收的广播

```xml
 <receiver
            android:name=".BootCompleteReceiver"
            android:enabled="true"
            android:exported="true">
	<intent-filter>
		<action android:name="android.intent.action.BOOT_COMPLETED" />
	</intent-filter>
</receiver>
```



## 发送自定义广播

### 标准广播（进程内起作用）

 在发送广播前需要先创建一个广播接收器用来接收这个广播，通过as创一个新的接收器，代码如下：

```java
package com.srcgzjiang.broadcasttest;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class MyBroadcastReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        // TODO: This method is called when the BroadcastReceiver is receiving
        // an Intent broadcast.
        
         Toast.makeText(context, "received in myBroadcastReceiver", 					Toast.LENGTH_SHORT).show();
        
        throw new UnsupportedOperationException("Not yet implemented");
    }
}
```

在这里收到自定义广播后，就有相应的弹窗，接下来需要在 AndroidManifest.xml 中定义要接收的广播类型

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
	package="com.example.broadcasttest">
	...
	<application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/AppTheme">
    	...
        <receiver
            android:name=".MyBroadcastReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                //这里就是定义好的广播，等会我们就要定义好这样一条广播
           		<action android:name="com.example.broadcasttest.MY_BROADCAST"/>
            </intent-filter>
        </receiver>
    </application>
</manifest>
```

接下来我们在 activity_main.xml 中添加一个按钮，用来发送广播

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical"
    android:layout_width="match_parent"
    android:layout_height="match_parent" >
    <Button
        android:id="@+id/button"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Send Broadcast"
        />
</LinearLayout>
```

然后就是给按钮添加响应事件

```java
 Button button = findViewById(R.id.button);
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                //intent里面的内容就是我们自定义的广播
                Intent intent = new Intent("com.example.broadcasttest.MY_BROADCAST");
                //发送广播
                sendBroadcast(intent);
            }
        });
```

这样就可以了

## 具体实践，实现强制下线功能

这个实践会将相关知识一起运用





# 数据持久化

## 将数据存储到文件中

Context类中提供了一个openFileOutput()方法，可以用于将数据存储到指定的文件中。

这个方法接收两个参数：

​	第一个参数是文件名，在文件创建的时候使用，注意这里指定的文件名不可以包含路径，因为所有的文件都默认存储到/data/data/<package name>/files/目录下；

​	第二个参数是文件的操作模式，主要有MODE_PRIVATE和MODE_APPEND两种模式可选，默认是MODE_PRIVATE，表示当指定相同文件名的时候，所写入的内容将会覆盖原文件中的内容，而MODE_APPEND则表示如果该文件已存在，就往文件里面追加内容，不存在就创建新文件。



