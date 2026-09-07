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
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
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
