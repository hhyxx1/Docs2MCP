import { FlutterPlugin, FlutterPluginBinding, MethodCall, MethodCallHandler, MethodChannel, MethodResult } from "@ohos/flutter_ohos";

export default class Docs2MCPPlugin implements FlutterPlugin, MethodCallHandler {
  private channel: MethodChannel | null = null;

  getUniqueClassName(): string {
    return "Docs2MCPPlugin";
  }

  onMethodCall(call: MethodCall, result: MethodResult): void {
    switch (call.method) {
      case "getPlatformVersion":
        result.success("HarmonyOS " + this.getHarmonyOSVersion());
        break;
      case "getDeviceInfo":
        result.success(this.getDeviceInfo());
        break;
      default:
        result.notImplemented();
    }
  }

  onAttachedToEngine(binding: FlutterPluginBinding): void {
    this.channel = new MethodChannel(binding.getBinaryMessenger(), "docs2mcp_plugin");
    this.channel.setMethodCallHandler(this);
  }

  onDetachedFromEngine(binding: FlutterPluginBinding): void {
    if (this.channel != null) {
      this.channel.setMethodCallHandler(null);
    }
  }

  private getHarmonyOSVersion(): string {
    // Get HarmonyOS version
    return "4.0.0";
  }

  private getDeviceInfo(): Record<string, string> {
    // Get device info
    return {
      deviceName: "HarmonyOS Device",
      deviceType: "smartphone",
      osVersion: this.getHarmonyOSVersion(),
      platform: "harmonyos"
    };
  }
}
