// Minimal UIKit shell for iPad mini 1st gen (A5/armv7, iOS 8+).
// Uses only iOS 8 APIs: UIApplicationMain, UIWindow, UIViewController.
// The game itself (Mindustry Classic jars) is loaded in a later step by a
// JVM-as-library loader; this file proves the Linux->armv7 link + packaging.
#import <UIKit/UIKit.h>

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end

@implementation AppDelegate
- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)options
{
    // NOTE: no -[UIScreen bounds] here: the trimmed theos SDK stubs lack
    // _objc_msgSend_stret (armv7 struct-return helper). Fixed frame is fine
    // for this scaffold; the full game glue will use complete Xcode stubs.
    self.window = [[UIWindow alloc] initWithFrame:CGRectMake(0, 0, 1024, 768)];
    UIViewController *vc = [UIViewController new];
    UILabel *label = [[UILabel alloc] initWithFrame:CGRectMake(20, 100, 280, 44)];
    label.text = @"Mindustry Classic iOS8 armv7";
    [vc.view addSubview:label];
    vc.view.backgroundColor = [UIColor whiteColor];
    self.window.rootViewController = vc;
    [self.window makeKeyAndVisible];
    return YES;
}
@end

int main(int argc, char *argv[])
{
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil,
                                 NSStringFromClass([AppDelegate class]));
    }
}
