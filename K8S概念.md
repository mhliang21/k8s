K8s如何工作：容器编排&声明式系统
-API Server
通过YAML或命令行提交资源定义（deployment、service）到API Server
-Controller Manager
"守护进程"，检查集群状态该是否符合预期，如果不符合就进行调整
-etcd
存储所有资源的状态信息
-资源类型（通过yaml定义）：
    -pod（含1个或n个容器）
    -ReplicaSet
    -deployment：管理pod副本数量
      - **核心功能**：管理 Pod 和 ReplicaSet 的声明式配置，支持滚动更新、回滚、扩缩容等。  
      - **应用场景**：  
        1. **滚动升级**：逐步替换旧版本 Pod，确保服务不中断（如更新镜像版本）。  
        2. **副本控制**：通过 `replicas` 字段动态调整 Pod 数量，应对流量波动。  
        3. **回滚机制**：记录历史版本，快速恢复至稳定状态（如 `kubectl rollout undo`）。  
    -service:  
      - **核心功能**：为 Pod 提供稳定的访问入口，支持负载均衡和服务发现。  
      - **应用场景**：  
        1. **ClusterIP**：内部服务通信，默认类型，适用于微服务间 API 调用。  
        2. **NodePort**：通过节点 IP 和静态端口暴露服务，适合临时外部访问（如开发测试）。  
        3. **LoadBalancer**：结合云厂商负载均衡器，对外提供高可用服务（如生产环境 Web 应用）。
| **类型**      | **访问范围**          | **端口特性**               | **适用场景**               |  
|---------------|-----------------------|---------------------------|--------------------------|  
| **ClusterIP** | 集群内部              | 虚拟 IP，仅集群内可访问     | 微服务间通信（如数据库服务） |  
| **NodePort**  | 集群外通过节点 IP     | 静态端口（30000-32767）    | 开发测试或临时外部访问 |  
| **LoadBalancer** | 外部网络（通过云 LB） | 自动分配公网 IP 和端口      | 生产环境高可用服务 |  
```yaml
apiVersion: kuration.io/v1
kind: InspectionTask  # 自定义资源类型
metadata:
  name: check-database
spec:
  schedule: "*/5 * * * *"  # 每 5 分钟执行一次
  target: "mysql-service"   # 巡检目标
  rules: [...]              # 巡检规则
```

概念：
-Helm：
  K8s包管理工具
  -CRD和Controller在不同Chart原因：V3 无法不会管理CRD的升级和删除；
  -解决方案：分为CRD Chart和Controller Chart;
-Chart：
  预配置的资源包，是Helm的打包格式，包含K8s需要的配置文件（deployment、service、configmap）和模板；
-CRD（Custom Resource Definitions）
  用来扩展K8s API；假设有新的资源类型，比如InspectionTask（巡检任务），提交CRD后，会注册到API Server中，然后就可以使用kubectl create inspectiontask xxx来创建巡检任务了。即CRD就像一个“类”，而具体的巡检任务就是这个类的实例。
-Controller：
  -监听资源：监听API Server中的资源变化，执行InspectionTask创建/更新/删除操作；
  -执行业务：如根据InspectionTask的spec中规则，生成一个定时任务cronJob定时任务，执行巡检任务；
-NFS（持久化存储）：
    默认pod无状态，当删除或重启，其内部存储丢失，pod挂载NFS存储，存储巡检结果；
    NFS管理方式：
        1、PV  预先创建NFS存储
        2、PVC（pod进行申请资源声明）
-Device Plugin：
    原生K8s只能调度CPU和内存资源，DP能让K8S发现和管理GPU资源。
    可使用Nvidia官方提供的插件，也可以自己Device Plugin。
-Daemonset：
    一种Controller，它确保在每个节点上运行一个 Pod 副本。
    -场景：如Clico、Flannel等网络组件需要每个节点上运行一个 Pod，处理容器网络流量；如日志收集、device plugin场景、存储场景；
-适配器adapter模式：
  - **适配器模式**，是处理多版本兼容的经典方案。将不同版本接口转换为另一个接口，以便客户端可以使用新接口。
  -解决接口不兼容、版本差异或系统集成问题，统一格式，实现兼容和解耦。
  -应用场景：
    1、解决不同版本接口不兼容的问题；
    2、集成外部系统到K8s，如开发一个CRD Adapter，将EC2实例抽象为VirtualMachine 资源；
    3、兼容不同容器运行时（Docker、containerd、CRI-O），其接口不同；
    4、自定义监控/日志采集；
    5、需统一管理多个异构集群（不同云厂商、版本）；
    6、自定义设备或硬件。通过Device Plugin框架开发Apapter，将硬件能力暴露给K8（NVIDIA GPU Adapter）；
  -operator：
    一种特殊的Controller，它负责管理和维护一个特定的资源类型，
- JFrog ML
  模型管理
  模型安全扫描
- Volcano
  Kubernetes 批处理调度引擎，专注于高性能计算（HPC）场景。 
- Thanos
  Prometheus 长期存储与高可用解决方案。  







附录：
### **CRD完整流程示例 **
#### 1. **定义 CRD**
- 创建一个 YAML 文件 `inspectiontask-crd.yaml`，定义 `InspectionTask` 的结构。
- 通过 `kubectl apply -f inspectiontask-crd.yaml` 提交到 Kubernetes。

#### 2. **开发 Controller**
- 编写 Controller 代码（比如用 Go 语言），监听 `InspectionTask` 资源。
- 当检测到新的 `InspectionTask` 时，创建对应的 CronJob 和 Pod。

#### 3. **打包为 Helm Chart**
- **Kuration-Server-CRD Chart**：
  - 仅包含 `crds/inspectiontask-crd.yaml`。
  - 通过 `helm install kuration-crd ./kuration-server-crd` 安装。
- **Kuration-Server-Controller Chart**：
  - 包含 Controller 的 Deployment、Service、RBAC 权限等。
  - 通过 `helm install kuration-controller ./kuration-server-controller` 安装。

#### 4. **用户如何使用**
- 用户安装 CRD Chart。
- 用户安装 Controller Chart。
- 用户提交自定义资源：
  ```yaml
  apiVersion: kuration.io/v1
  kind: InspectionTask
  metadata:
    name: check-database
  spec:
    schedule: "*/5 * * * *"
    target: "mysql-service"
  ```
- Controller 检测到该资源，创建定时任务执行巡检。

---

### **关键总结**
| 概念            | 作用                          | 类比                  |
|-----------------|-----------------------------|----------------------|
| Kubernetes API  | 接收资源定义，存储到 etcd       | 政府办事大厅（接收申请） |
| CRD             | 扩展 Kubernetes 的“资源类型”   | 在政府注册新的业务类型   |
| Controller      | 监听资源变化，执行业务逻辑       | 专门处理某类业务的办事员 |
| Helm Chart      | 打包应用的所有资源和配置         | 软件的安装包           |
| CRD Chart       | 仅包含自定义资源定义             | 安装前的“注册许可证”    |
| Controller Chart| 包含业务逻辑和依赖资源           | 软件的“主程序”         |

---
