# STEP-013 Evidence Manifest

审查日期：2026-09-09。原始证据位于本机
`D:\Codex\eink-panel\hardware\evidence\STEP013_PENDING`，仅本地保留并由 `.gitignore`
精确忽略；本清单不包含或改写原始文件。共 26 个文件：23 张 JPG、3 份 PDF。

哈希算法：SHA-256。Observation 仅记录逐文件实际可见内容，不根据随机文件名推断。
`PASS` 仅代表照片中未见明显外观损伤；不代表电气、运行或显示验证。

| ID | File | Bytes | SHA-256 | Evidence Type | Observation / Use | Confidence |
| ---: | --- | ---: | --- | --- | --- | --- |
| E01 | `0641F54C722E17BC50A0D025960CCEE2.jpg` | 11003888 | `8c4eb6f106583a8c3a51b475794ae82008a75399012ca6e4da549e13a95ff95e` | Physical photo | ESP32-M1 正面局部；可见 ESP32-WROOM-32D、P4、P5 及板载接口。 | High |
| E02 | `1791e76bbba62347dc156f88df751e07.jpg` | 8694279 | `d47f73d292c1893839e7dd269e201bd7014ad0b1d2ecfe5a136c84cbdd239e91` | Physical close-up | P4 的 `2.2/0.47` 丝印、滑块位置及 P5/P6/P7 接口局部。支持滑块位于 2.2 一侧。 | High |
| E03 | `1847B84769C4F0738B856831308D9591.jpg` | 576660 | `b72f789ee75b5fa283c2fe3bdd5f24e57b8410976b9e410bf0dee38d2274c8af` | Physical photo | ESP32-M1 正面全貌；USB 与 FPC 未连接。 | Medium |
| E04 | `20BC9FD5798976386B2048FAE8A462A0.jpg` | 9440667 | `03646a33a8f1824ebed8cac52491a2173e41cb2df8ed7a857bfee1857b4ea743` | Physical photo | ESP32-M1 PCB 背面及 Good Display 标识。 | High |
| E05 | `3265EA3F3569F66621F249BB1CFFF084.jpg` | 10776557 | `d8d10df5e3ea4587f6d1ad5f38b15f48a2e6f5f44696f37eac981d604098d097` | Physical close-up | ESP32-M1、WROOM-32D、P4 和 P5 区域的另一角度。 | High |
| E06 | `427A84CB6FEEB5A6326C1554E6A806A9.jpg` | 627906 | `5ab2bb686371a88308d6fe90e84788182a8309b7aa38f5fe43d9934153f1e375` | Physical photo | 屏幕背面、FPC 与标签 `042BN-T81-D2`。 | High |
| E07 | `4DE244E18CAEBBE47BCC4DF97B443D7B.jpg` | 9020819 | `55b06bc88b1afbce9e5a74acb8ee2fc289988c370e73308722084a4115f843d7` | Physical photo | ESP32-M1 侧视；补充接口机械外观，不用于电气结论。 | Medium |
| E08 | `52AE9B9BED90B31471A3C0E9C4D89E1B.jpg` | 9411366 | `f1f7f5f5b689f0c6233b37329b4adc5a63a46eab2a7bcffe6588c1e729b9485c` | Physical photo | ESP32-M1 正面全貌；支持当前实物板身份。 | High |
| E09 | `59D53903125F330A12F31BA4B2B96511.jpg` | 1588083 | `c52d7378dd7599b05d3068f07642395c42e6e10c80ef74dfb6e4f56e26084c44` | Physical close-up | P4 丝印与滑块的清晰近照；支持 `RESE_ACTUAL=2.2Ω` 的视觉档位判断。 | High |
| E10 | `8155A2DE0A1A25D9C0ACAC68F23F01A0.jpg` | 7869024 | `17d1416f37efc75e2be1dad8f7f9854e3867a1cf46c47923162e833318b904ea` | Physical close-up | 屏幕背标 `042BN-T81-D2`、FPC 走线及接触端；未见明显损伤。 | High |
| E11 | `A099C39F36E43042D69AE1D235AE332A.jpg` | 518564 | `d4ca99bdc77c7c1c0f2dd50698b69cbcbb1c9cc514dd5e05d9e36fd4820347b1` | Supplementary photo | 备用 NodeMCU/ESP32 开发板正面；非 ESP32-M1 主路线，不参与 Gate。 | High |
| E12 | `A2585B45334477C1FE6671934D621546.jpg` | 6974947 | `9856b56dd227ffa0957cfc5c644c7fc33b4cf37373036d4e265bac1deb2e09f4` | Physical photo | ESP32-M1 另一侧视角；补充机械外观。 | Medium |
| E13 | `A711E9B9395EB78D9951E70E9949AB20.jpg` | 11527741 | `a1d6baac48488348323a66e30a53f7a669118248bf9489a7381bceea1af5593a` | Physical photo | ESP32-M1 正面完整清晰视图，可见 WROOM-32D、P4、P5。 | High |
| E14 | `B0E4ED40D3F17D1AEA1E1CD2FBFFAFF9.jpg` | 454700 | `d39165fb386fa7706ebeedbc2a9a2d5eb8f79188ad84e6ad54fc24a7e4c2e56a` | Physical photo | ESP32-M1 PCB 背面全貌及 Good Display 标识。 | High |
| E15 | `B19AEF54A85048D61FB5738361DF6C52.jpg` | 6631329 | `0ae67bb8e7d0223c3d45001b0f095751aa899780abc5e6546ff82282becc8ca7` | Context photo | 屏幕、ESP32-M1 和备用 NodeMCU 均未连接；用于整体物料上下文。 | Medium |
| E16 | `B7441E696D9C9B3F4116322BB62F2845.jpg` | 7552981 | `40689d3b05bbc6a70725a3c3b00120d3a8894ea7c7d1114863f97c928ea3dd22` | Physical photo | ESP32-M1 PCB 背面另一视角。 | Medium |
| E17 | `BA4530A9C40B398562B438918BC46210.jpg` | 10516605 | `b5f877838df402843c4b13c13d5d56e1cab9c8104d29404049d53481dce36a89` | Physical close-up | P4、P5、WROOM-32D 清晰局部；支持板、接口和档位交叉核对。 | High |
| E18 | `C991A3463049E2DC2F66150E71F476D6.jpg` | 6267171 | `3593ac478faea3cd03902d39b950936990521438b2589354f86ac5c71b039c1e` | Supplementary photo | UNI-T UT123D 包装；只证明仪表物料存在，不证明测量或校准。 | High |
| E19 | `catalog-cn.pdf` | 6033501 | `7586e5f07ff8415e956084fdfad533c601ad42c14a6a71a2e32949d71f375c7b` | Official catalog | 第 4 页列出 GDEY042T81、4.2 英寸、400×300；不直接映射实物背标。 | High |
| E20 | `D0CEE37DC407A42243AB28AC3D8AF5D7.jpg` | 8704065 | `8ef1f7f8c059ddedc2fe1b86bdb18840c18351d5d9140eb5e5601c9342e967ff` | Physical close-up | WROOM-32D、P4 与板上 `ESP32-M1` 丝印；支持当前档位交叉核对。 | High |
| E21 | `d6495b144a434a0bbef2a511ad74192f.jpg` | 43775 | `3f53bcccfea54a0d05d903ad6b6fd2c908ab4b89958bbf3f403bcf1aa231a1c7` | Seller confirmation | 用户确认该图由卖家针对本次屏幕提供；列出 GDEY042T81、4.2 英寸、SSD1683、400×300、24 Pin/0.5mm、黑白和 SPI。 | High, source attested by user |
| E22 | `D7B0993E5A6E01DEDE09957F33602041.jpg` | 7510042 | `97d37ae0b07eccf42a7dd731cc8fa7c44955d601ab4a89e145a6b61ce91f20dd` | Physical close-up | 屏幕正面边缘及 FPC 接触端；未见明显撕裂、严重折痕、分层或烧损。 | High |
| E23 | `E325EE5EF307A678DAD43A1A70E9813B.jpg` | 449352 | `bdbb12adb5e246fa659c30a56afc1b834e8a73736a4fc970a516262577fbff2b` | Supplementary photo | 备用 NodeMCU/ESP-32S 背面；非 ESP32-M1 主路线，不参与 Gate。 | High |
| E24 | `EEAF4C09E2E6B66D5437BEE738778C61.jpg` | 12345938 | `0f8ee7268d16e9927f944a06254d1e4eadc6a18b65154c5381f1c31dff90a069` | Physical close-up | ESP32-M1 的 P5 24-pin 接口及相邻 P6/P7；P5 当前为空。 | High |
| E25 | `ESP32-M1 V1.0.pdf` | 926586 | `60595f7d9aefdcd5d7257354476d9236eb83f4ff61e9d48e68d898ea0c217b7e` | Official manual | 第 6 页确认 P4 RESE 规则、P5 24-pin、显示面朝上及锁扣操作；本步骤不执行操作。 | High |
| E26 | `ESP32-M1-SCH-20260307.pdf` | 460102 | `06baa8124052e4762e1d2bf6642f4371e2bdc620da246b8f4c704e418fd9f4bf` | Official schematic | 唯一页确认 WROOM-32D、P5 电气引脚、GPIO、3.3V 稳压和电子纸升压网络。 | High |

## Privacy and integrity decision

- 逐图检查未见订单号、地址、聊天账号、Token、密码或面部信息；部分照片包含手部、桌面和无关物料。
- 原始证据体积较大且属于本地实物记录，因此不进入 Git；只提交本 Manifest、审查结论和精确忽略规则。
- 卖家确认图没有显示订单号或聊天上下文；其“对应本次购买”的来源归属来自用户明确确认，已与图内可见规格分开记录。
- 后续复核时先重新计算 SHA-256；任何哈希变化都必须视为新证据，不能沿用本清单观察结论。

## Evidence-level conclusion

P4 滑块档位、P5 身份、屏幕 FPC 外观和营销型号证据已经满足 STEP-013 文档收口。
实物 PCB 修订号、FPC 实物 Pin 1、任何电阻/电压/连续性、BUSY、刷新及显示结果仍未验证，
但它们属于 STEP-014 或 H0 物理测试，不阻塞本次证据级 Gate。
