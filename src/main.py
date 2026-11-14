import flet as ft
import json
import time
import math
import traceback
import asyncio
import urllib.request
import urllib.parse
from market_feed import FeedError, SessionExpired
from server_feed import ServerAngelFeed, ServerDhanReadOnly, DHAN_VERIFIED_SYMBOLS
from analysis_quality import quality_check, agreement_detail
from chart_indicators import chart_indicators
from help_content import describe
from i18n import localize_tree,translate
from snapshot_store import SnapshotStore,age_label
from feed_health import FeedHealth,safe_error,retry_delay
from error_doctor import diagnose
from preference_store import PreferenceWriter,load_preferences
from storage_paths import storage_paths
from paper_engine import levels,pnl as paper_pnl,validate_expiry,risk_check,evaluate_mark,finite
from scanner_engine import DEFAULT_FILTERS, OPTION_FILTERS, ALL_FILTERS, analyze, rank_candidates
from datetime import datetime, date, timedelta, timezone
from importlib.metadata import version as package_version, PackageNotFoundError

try:
    APP_VERSION = package_version("bot-king")
except PackageNotFoundError:
    APP_VERSION = "2.3.102"  # Release fallback; CI verifies equality with pyproject.toml.
from pathlib import Path

#                                  Apache License
#                            Version 2.0, January 2004
#                         http://www.apache.org/licenses/
# 
#    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
# 
#    1. Definitions.
# 
#       "License" shall mean the terms and conditions for use, reproduction,
#       and distribution as defined by Sections 1 through 9 of this document.
# 
#       "Licensor" shall mean the copyright owner or entity authorized by
#       the copyright owner that is granting the License.
# 
#       "Legal Entity" shall mean the union of the acting entity and all
#       other entities that control, are controlled by, or are under common
#       control with that entity. For the purposes of this definition,
#       "control" means (i) the power, direct or indirect, to cause the
#       direction or management of such entity, whether by contract or
#       otherwise, or (ii) ownership of fifty percent (50%) or more of the
#       outstanding shares, or (iii) beneficial ownership of such entity.
# 
#       "You" (or "Your") shall mean an individual or Legal Entity
#       exercising permissions granted by this License.
# 
#       "Source" form shall mean the preferred form for making modifications,
#       including but not limited to software source code, documentation
#       source, and configuration files.
# 
#       "Object" form shall mean any form resulting from mechanical
#       transformation or translation of a Source form, including but
#       not limited to compiled object code, generated documentation,
#       and conversions to other media types.
# 
#       "Work" shall mean the work of authorship, whether in Source or
#       Object form, made available under the License, as indicated by a
#       copyright notice that is included in or attached to the work
#       (an example is provided in the Appendix below).
# 
#       "Derivative Works" shall mean any work, whether in Source or Object
#       form, that is based on (or derived from) the Work and for which the
#       editorial revisions, annotations, elaborations, or other modifications
#       represent, as a whole, an original work of authorship. For the purposes
#       of this License, Derivative Works shall not include works that remain
#       separable from, or merely link (or bind by name) to the interfaces of,
#       the Work and Derivative Works thereof.
# 
#       "Contribution" shall mean any work of authorship, including
#       the original version of the Work and any modifications or additions
#       to that Work or Derivative Works thereof, that is intentionally
#       submitted to Licensor for inclusion in the Work by the copyright owner
#       or by an individual or Legal Entity authorized to submit on behalf of
#       the copyright owner. For the purposes of this definition, "submitted"
#       means any form of electronic, verbal, or written communication sent
#       to the Licensor or its representatives, including but not limited to
#       communication on electronic mailing lists, source code control systems,
#       and issue tracking systems that are managed by, or on behalf of, the
#       Licensor for the purpose of discussing and improving the Work, but
#       excluding communication that is conspicuously marked or otherwise
#       designated in writing by the copyright owner as "Not a Contribution."
# 
#       "Contributor" shall mean Licensor and any individual or Legal Entity
#       on behalf of whom a Contribution has been received by Licensor and
#       subsequently incorporated within the Work.
# 
#    2. Grant of Copyright License. Subject to the terms and conditions of
#       this License, each Contributor hereby grants to You a perpetual,
#       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
#       copyright license to reproduce, prepare Derivative Works of,
#       publicly display, publicly perform, sublicense, and distribute the
#       Work and such Derivative Works in Source or Object form.
# 
#    3. Grant of Patent License. Subject to the terms and conditions of
#       this License, each Contributor hereby grants to You a perpetual,
#       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
#       (except as stated in this section) patent license to make, have made,
#       use, offer to sell, sell, import, and otherwise transfer the Work,
#       where such license applies only to those patent claims licensable
#       by such Contributor that are necessarily infringed by their
#       Contribution(s) alone or by combination of their Contribution(s)
#       with the Work to which such Contribution(s) was submitted. If You
#       institute patent litigation against any entity (including a
#       cross-claim or counterclaim in a lawsuit) alleging that the Work
#       or a Contribution incorporated within the Work constitutes direct
#       or contributory patent infringement, then any patent licenses
#       granted to You under this License for that Work shall terminate
#       as of the date such litigation is filed.
# 
#    4. Redistribution. You may reproduce and distribute copies of the
#       Work or Derivative Works thereof in any medium, with or without
#       modifications, and in Source or Object form, provided that You
#       meet the following conditions:
# 
#       (a) You must give any other recipients of the Work or
#           Derivative Works a copy of this License; and
# 
#       (b) You must cause any modified files to carry prominent notices
#           stating that You changed the files; and
# 
#       (c) You must retain, in the Source form of any Derivative Works
#           that You distribute, all copyright, patent, trademark, and
#           attribution notices from the Source form of the Work,
#           excluding those notices that do not pertain to any part of
#           the Derivative Works; and
# 
#       (d) If the Work includes a "NOTICE" text file as part of its
#           distribution, then any Derivative Works that You distribute must
#           include a readable copy of the attribution notices contained
#           within such NOTICE file, excluding those notices that do not
#           pertain to any part of the Derivative Works, in at least one
#           of the following places: within a NOTICE text file distributed
#           as part of the Derivative Works; within the Source form or
#           documentation, if provided along with the Derivative Works; or,
#           within a display generated by the Derivative Works, if and
#           wherever such third-party notices normally appear. The contents
#           of the NOTICE file are for informational purposes only and
#           do not modify the License. You may add Your own attribution
#           notices within Derivative Works that You distribute, alongside
#           or as an addendum to the NOTICE text from the Work, provided
#           that such additional attribution notices cannot be construed
#           as modifying the License.
# 
#       You may add Your own copyright statement to Your modifications and
#       may provide additional or different license terms and conditions
#       for use, reproduction, or distribution of Your modifications, or
#       for any such Derivative Works as a whole, provided Your use,
#       reproduction, and distribution of the Work otherwise complies with
#       the conditions stated in this License.
# 
#    5. Submission of Contributions. Unless You explicitly state otherwise,
#       any Contribution intentionally submitted for inclusion in the Work
#       by You to the Licensor shall be under the terms and conditions of
#       this License, without any additional terms or conditions.
#       Notwithstanding the above, nothing herein shall supersede or modify
#       the terms of any separate license agreement you may have executed
#       with Licensor regarding such Contributions.
# 
#    6. Trademarks. This License does not grant permission to use the trade
#       names, trademarks, service marks, or product names of the Licensor,
#       except as required for reasonable and customary use in describing the
#       origin of the Work and reproducing the content of the NOTICE file.
# 
#    7. Disclaimer of Warranty. Unless required by applicable law or
#       agreed to in writing, Licensor provides the Work (and each
#       Contributor provides its Contributions) on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#       implied, including, without limitation, any warranties or conditions
#       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
#       PARTICULAR PURPOSE. You are solely responsible for determining the
#       appropriateness of using or redistributing the Work and assume any
#       risks associated with Your exercise of permissions under this License.
# 
#    8. Limitation of Liability. In no event and under no legal theory,
#       whether in tort (including negligence), contract, or otherwise,
#       unless required by applicable law (such as deliberate and grossly
#       negligent acts) or agreed to in writing, shall any Contributor be
#       liable to You for damages, including any direct, indirect, special,
#       incidental, or consequential damages of any character arising as a
#       result of this License or out of the use or inability to use the
#       Work (including but not limited to damages for loss of goodwill,
#       work stoppage, computer failure or malfunction, or any and all
#       other commercial damages or losses), even if such Contributor
#       has been advised of the possibility of such damages.
# 
#    9. Accepting Warranty or Additional Liability. While redistributing
#       the Work or Derivative Works thereof, You may choose to offer,
#       and charge a fee for, acceptance of support, warranty, indemnity,
#       or other liability obligations and/or rights consistent with this
#       License. However, in accepting such obligations, You may act only
#       on Your own behalf and on Your sole responsibility, not on behalf
#       of any other Contributor, and only if You agree to indemnify,
#       defend, and hold each Contributor harmless for any liability
#       incurred by, or claims asserted against, such Contributor by reason
#       of your accepting any such warranty or additional liability.
# 
#    END OF TERMS AND CONDITIONS
# 
#    APPENDIX: How to apply the Apache License to your work.
# 
#       To apply the Apache License to your work, attach the following
#       boilerplate notice, with the fields enclosed by brackets "[]"
#       replaced with your own identifying information. (Don't include
#       the brackets!)  The text should be enclosed in the appropriate
#       comment syntax for the file format. We also recommend that a
#       file or class name and description of purpose be included on the
#       same "printed page" as the copyright notice for easier
#       identification within third-party archives.
# 
#    Copyright 2023 TradingView, Inc.
# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# 
LIGHTWEIGHT_CHARTS_JS="/*!\n * @license\n * TradingView Lightweight Charts™ v4.2.3\n * Copyright (c) 2025 TradingView, Inc.\n * Licensed under Apache License 2.0 https://www.apache.org/licenses/LICENSE-2.0\n */\n!function(){\"use strict\";const t={upColor:\"#26a69a\",downColor:\"#ef5350\",wickVisible:!0,borderVisible:!0,borderColor:\"#378658\",borderUpColor:\"#26a69a\",borderDownColor:\"#ef5350\",wickColor:\"#737375\",wickUpColor:\"#26a69a\",wickDownColor:\"#ef5350\"},i={upColor:\"#26a69a\",downColor:\"#ef5350\",openVisible:!0,thinBars:!0},n={color:\"#2196f3\",lineStyle:0,lineWidth:3,lineType:0,lineVisible:!0,crosshairMarkerVisible:!0,crosshairMarkerRadius:4,crosshairMarkerBorderColor:\"\",crosshairMarkerBorderWidth:2,crosshairMarkerBackgroundColor:\"\",lastPriceAnimation:0,pointMarkersVisible:!1},s={topColor:\"rgba( 46, 220, 135, 0.4)\",bottomColor:\"rgba( 40, 221, 100, 0)\",invertFilledArea:!1,lineColor:\"#33D778\",lineStyle:0,lineWidth:3,lineType:0,lineVisible:!0,crosshairMarkerVisible:!0,crosshairMarkerRadius:4,crosshairMarkerBorderColor:\"\",crosshairMarkerBorderWidth:2,crosshairMarkerBackgroundColor:\"\",lastPriceAnimation:0,pointMarkersVisible:!1},e={baseValue:{type:\"price\",price:0},topFillColor1:\"rgba(38, 166, 154, 0.28)\",topFillColor2:\"rgba(38, 166, 154, 0.05)\",topLineColor:\"rgba(38, 166, 154, 1)\",bottomFillColor1:\"rgba(239, 83, 80, 0.05)\",bottomFillColor2:\"rgba(239, 83, 80, 0.28)\",bottomLineColor:\"rgba(239, 83, 80, 1)\",lineWidth:3,lineStyle:0,lineType:0,lineVisible:!0,crosshairMarkerVisible:!0,crosshairMarkerRadius:4,crosshairMarkerBorderColor:\"\",crosshairMarkerBorderWidth:2,crosshairMarkerBackgroundColor:\"\",lastPriceAnimation:0,pointMarkersVisible:!1},r={color:\"#26a69a\",base:0},h={color:\"#2196f3\"},l={title:\"\",visible:!0,lastValueVisible:!0,priceLineVisible:!0,priceLineSource:0,priceLineWidth:1,priceLineColor:\"\",priceLineStyle:2,baseLineVisible:!0,baseLineWidth:1,baseLineColor:\"#B2B5BE\",baseLineStyle:0,priceFormat:{type:\"price\",precision:2,minMove:.01}};var a,o;function _(t,i){const n={0:[],1:[t.lineWidth,t.lineWidth],2:[2*t.lineWidth,2*t.lineWidth],3:[6*t.lineWidth,6*t.lineWidth],4:[t.lineWidth,4*t.lineWidth]}[i];t.setLineDash(n)}function u(t,i,n,s){t.beginPath();const e=t.lineWidth%2?.5:0;t.moveTo(n,i+e),t.lineTo(s,i+e),t.stroke()}function c(t,i){if(!t)throw new Error(\"Assertion failed\"+(i?\": \"+i:\"\"))}function d(t){if(void 0===t)throw new Error(\"Value is undefined\");return t}function f(t){if(null===t)throw new Error(\"Value is null\");return t}function v(t){return f(d(t))}!function(t){t[t.Simple=0]=\"Simple\",t[t.WithSteps=1]=\"WithSteps\",t[t.Curved=2]=\"Curved\"}(a||(a={})),function(t){t[t.Solid=0]=\"Solid\",t[t.Dotted=1]=\"Dotted\",t[t.Dashed=2]=\"Dashed\",t[t.LargeDashed=3]=\"LargeDashed\",t[t.SparseDotted=4]=\"SparseDotted\"}(o||(o={}));const p={khaki:\"#f0e68c\",azure:\"#f0ffff\",aliceblue:\"#f0f8ff\",ghostwhite:\"#f8f8ff\",gold:\"#ffd700\",goldenrod:\"#daa520\",gainsboro:\"#dcdcdc\",gray:\"#808080\",green:\"#008000\",honeydew:\"#f0fff0\",floralwhite:\"#fffaf0\",lightblue:\"#add8e6\",lightcoral:\"#f08080\",lemonchiffon:\"#fffacd\",hotpink:\"#ff69b4\",lightyellow:\"#ffffe0\",greenyellow:\"#adff2f\",lightgoldenrodyellow:\"#fafad2\",limegreen:\"#32cd32\",linen:\"#faf0e6\",lightcyan:\"#e0ffff\",magenta:\"#f0f\",maroon:\"#800000\",olive:\"#808000\",orange:\"#ffa500\",oldlace:\"#fdf5e6\",mediumblue:\"#0000cd\",transparent:\"#0000\",lime:\"#0f0\",lightpink:\"#ffb6c1\",mistyrose:\"#ffe4e1\",moccasin:\"#ffe4b5\",midnightblue:\"#191970\",orchid:\"#da70d6\",mediumorchid:\"#ba55d3\",mediumturquoise:\"#48d1cc\",orangered:\"#ff4500\",royalblue:\"#4169e1\",powderblue:\"#b0e0e6\",red:\"#f00\",coral:\"#ff7f50\",turquoise:\"#40e0d0\",white:\"#fff\",whitesmoke:\"#f5f5f5\",wheat:\"#f5deb3\",teal:\"#008080\",steelblue:\"#4682b4\",bisque:\"#ffe4c4\",aquamarine:\"#7fffd4\",aqua:\"#0ff\",sienna:\"#a0522d\",silver:\"#c0c0c0\",springgreen:\"#00ff7f\",antiquewhite:\"#faebd7\",burlywood:\"#deb887\",brown:\"#a52a2a\",beige:\"#f5f5dc\",chocolate:\"#d2691e\",chartreuse:\"#7fff00\",cornflowerblue:\"#6495ed\",cornsilk:\"#fff8dc\",crimson:\"#dc143c\",cadetblue:\"#5f9ea0\",tomato:\"#ff6347\",fuchsia:\"#f0f\",blue:\"#00f\",salmon:\"#fa8072\",blanchedalmond:\"#ffebcd\",slateblue:\"#6a5acd\",slategray:\"#708090\",thistle:\"#d8bfd8\",tan:\"#d2b48c\",cyan:\"#0ff\",darkblue:\"#00008b\",darkcyan:\"#008b8b\",darkgoldenrod:\"#b8860b\",darkgray:\"#a9a9a9\",blueviolet:\"#8a2be2\",black:\"#000\",darkmagenta:\"#8b008b\",darkslateblue:\"#483d8b\",darkkhaki:\"#bdb76b\",darkorchid:\"#9932cc\",darkorange:\"#ff8c00\",darkgreen:\"#006400\",darkred:\"#8b0000\",dodgerblue:\"#1e90ff\",darkslategray:\"#2f4f4f\",dimgray:\"#696969\",deepskyblue:\"#00bfff\",firebrick:\"#b22222\",forestgreen:\"#228b22\",indigo:\"#4b0082\",ivory:\"#fffff0\",lavenderblush:\"#fff0f5\",feldspar:\"#d19275\",indianred:\"#cd5c5c\",lightgreen:\"#90ee90\",lightgrey:\"#d3d3d3\",lightskyblue:\"#87cefa\",lightslategray:\"#789\",lightslateblue:\"#8470ff\",snow:\"#fffafa\",lightseagreen:\"#20b2aa\",lightsalmon:\"#ffa07a\",darksalmon:\"#e9967a\",darkviolet:\"#9400d3\",mediumpurple:\"#9370d8\",mediumaquamarine:\"#66cdaa\",skyblue:\"#87ceeb\",lavender:\"#e6e6fa\",lightsteelblue:\"#b0c4de\",mediumvioletred:\"#c71585\",mintcream:\"#f5fffa\",navajowhite:\"#ffdead\",navy:\"#000080\",olivedrab:\"#6b8e23\",palevioletred:\"#d87093\",violetred:\"#d02090\",yellow:\"#ff0\",yellowgreen:\"#9acd32\",lawngreen:\"#7cfc00\",pink:\"#ffc0cb\",paleturquoise:\"#afeeee\",palegoldenrod:\"#eee8aa\",darkolivegreen:\"#556b2f\",darkseagreen:\"#8fbc8f\",darkturquoise:\"#00ced1\",peachpuff:\"#ffdab9\",deeppink:\"#ff1493\",violet:\"#ee82ee\",palegreen:\"#98fb98\",mediumseagreen:\"#3cb371\",peru:\"#cd853f\",saddlebrown:\"#8b4513\",sandybrown:\"#f4a460\",rosybrown:\"#bc8f8f\",purple:\"#800080\",seagreen:\"#2e8b57\",seashell:\"#fff5ee\",papayawhip:\"#ffefd5\",mediumslateblue:\"#7b68ee\",plum:\"#dda0dd\",mediumspringgreen:\"#00fa9a\"};function m(t){return t<0?0:t>255?255:Math.round(t)||0}function b(t){return t<=0||t>1?Math.min(Math.max(t,0),1):Math.round(1e4*t)/1e4}const w=/^#([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?$/i,g=/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?$/i,M=/^rgb\\(\\s*(-?\\d{1,10})\\s*,\\s*(-?\\d{1,10})\\s*,\\s*(-?\\d{1,10})\\s*\\)$/,x=/^rgba\\(\\s*(-?\\d{1,10})\\s*,\\s*(-?\\d{1,10})\\s*,\\s*(-?\\d{1,10})\\s*,\\s*(-?\\d*\\.?\\d+)\\s*\\)$/;function S(t){(t=t.toLowerCase())in p&&(t=p[t]);{const i=x.exec(t)||M.exec(t);if(i)return[m(parseInt(i[1],10)),m(parseInt(i[2],10)),m(parseInt(i[3],10)),b(i.length<5?1:parseFloat(i[4]))]}{const i=g.exec(t);if(i)return[m(parseInt(i[1],16)),m(parseInt(i[2],16)),m(parseInt(i[3],16)),1]}{const i=w.exec(t);if(i)return[m(17*parseInt(i[1],16)),m(17*parseInt(i[2],16)),m(17*parseInt(i[3],16)),1]}throw new Error(`Cannot parse color: ${t}`)}function k(t){return.199*t[0]+.687*t[1]+.114*t[2]}function y(t){const i=S(t);return{t:`rgb(${i[0]}, ${i[1]}, ${i[2]})`,i:k(i)>160?\"black\":\"white\"}}class C{constructor(){this.h=[]}l(t,i,n){const s={o:t,_:i,u:!0===n};this.h.push(s)}v(t){const i=this.h.findIndex((i=>t===i.o));i>-1&&this.h.splice(i,1)}p(t){this.h=this.h.filter((i=>i._!==t))}m(t,i,n){const s=[...this.h];this.h=this.h.filter((t=>!t.u)),s.forEach((s=>s.o(t,i,n)))}M(){return this.h.length>0}S(){this.h=[]}}function T(t,...i){for(const n of i)for(const i in n)void 0!==n[i]&&Object.prototype.hasOwnProperty.call(n,i)&&![\"__proto__\",\"constructor\",\"prototype\"].includes(i)&&(\"object\"!=typeof n[i]||void 0===t[i]||Array.isArray(n[i])?t[i]=n[i]:T(t[i],n[i]));return t}function P(t){return\"number\"==typeof t&&isFinite(t)}function R(t){return\"number\"==typeof t&&t%1==0}function D(t){return\"string\"==typeof t}function O(t){return\"boolean\"==typeof t}function B(t){const i=t;if(!i||\"object\"!=typeof i)return i;let n,s,e;for(s in n=Array.isArray(i)?[]:{},i)i.hasOwnProperty(s)&&(e=i[s],n[s]=e&&\"object\"==typeof e?B(e):e);return n}function V(t){return null!==t}function A(t){return null===t?void 0:t}const z=\"-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif\";function E(t,i,n){return void 0===i&&(i=z),`${n=void 0!==n?`${n} `:\"\"}${t}px ${i}`}class I{constructor(t){this.k={C:1,T:5,P:NaN,R:\"\",D:\"\",O:\"\",B:\"\",V:0,A:0,I:0,L:0,N:0},this.F=t}W(){const t=this.k,i=this.j(),n=this.H();return t.P===i&&t.D===n||(t.P=i,t.D=n,t.R=E(i,n),t.L=2.5/12*i,t.V=t.L,t.A=i/12*t.T,t.I=i/12*t.T,t.N=0),t.O=this.$(),t.B=this.U(),this.k}$(){return this.F.W().layout.textColor}U(){return this.F.q()}j(){return this.F.W().layout.fontSize}H(){return this.F.W().layout.fontFamily}}class L{constructor(){this.Y=[]}Z(t){this.Y=t}X(t,i,n){this.Y.forEach((s=>{s.X(t,i,n)}))}}class N{X(t,i,n){t.useBitmapCoordinateSpace((t=>this.K(t,i,n)))}}class F extends N{constructor(){super(...arguments),this.G=null}J(t){this.G=t}K({context:t,horizontalPixelRatio:i,verticalPixelRatio:n}){if(null===this.G||null===this.G.tt)return;const s=this.G.tt,e=this.G,r=Math.max(1,Math.floor(i))%2/2,h=h=>{t.beginPath();for(let l=s.to-1;l>=s.from;--l){const s=e.it[l],a=Math.round(s.nt*i)+r,o=s.st*n,_=h*n+r;t.moveTo(a,o),t.arc(a,o,_,0,2*Math.PI)}t.fill()};e.et>0&&(t.fillStyle=e.rt,h(e.ht+e.et)),t.fillStyle=e.lt,h(e.ht)}}function W(){return{it:[{nt:0,st:0,ot:0,_t:0}],lt:\"\",rt:\"\",ht:0,et:0,tt:null}}const j={from:0,to:1};class H{constructor(t,i){this.ut=new L,this.ct=[],this.dt=[],this.ft=!0,this.F=t,this.vt=i,this.ut.Z(this.ct)}bt(t){const i=this.F.wt();i.length!==this.ct.length&&(this.dt=i.map(W),this.ct=this.dt.map((t=>{const i=new F;return i.J(t),i})),this.ut.Z(this.ct)),this.ft=!0}gt(){return this.ft&&(this.Mt(),this.ft=!1),this.ut}Mt(){const t=2===this.vt.W().mode,i=this.F.wt(),n=this.vt.xt(),s=this.F.St();i.forEach(((i,e)=>{var r;const h=this.dt[e],l=i.kt(n);if(t||null===l||!i.yt())return void(h.tt=null);const a=f(i.Ct());h.lt=l.Tt,h.ht=l.ht,h.et=l.Pt,h.it[0]._t=l._t,h.it[0].st=i.Dt().Rt(l._t,a.Ot),h.rt=null!==(r=l.Bt)&&void 0!==r?r:this.F.Vt(h.it[0].st/i.Dt().At()),h.it[0].ot=n,h.it[0].nt=s.zt(n),h.tt=j}))}}class $ extends N{constructor(t){super(),this.Et=t}K({context:t,bitmapSize:i,horizontalPixelRatio:n,verticalPixelRatio:s}){if(null===this.Et)return;const e=this.Et.It.yt,r=this.Et.Lt.yt;if(!e&&!r)return;const h=Math.round(this.Et.nt*n),l=Math.round(this.Et.st*s);t.lineCap=\"butt\",e&&h>=0&&(t.lineWidth=Math.floor(this.Et.It.et*n),t.strokeStyle=this.Et.It.O,t.fillStyle=this.Et.It.O,_(t,this.Et.It.Nt),function(t,i,n,s){t.beginPath();const e=t.lineWidth%2?.5:0;t.moveTo(i+e,n),t.lineTo(i+e,s),t.stroke()}(t,h,0,i.height)),r&&l>=0&&(t.lineWidth=Math.floor(this.Et.Lt.et*s),t.strokeStyle=this.Et.Lt.O,t.fillStyle=this.Et.Lt.O,_(t,this.Et.Lt.Nt),u(t,l,0,i.width))}}class U{constructor(t){this.ft=!0,this.Ft={It:{et:1,Nt:0,O:\"\",yt:!1},Lt:{et:1,Nt:0,O:\"\",yt:!1},nt:0,st:0},this.Wt=new $(this.Ft),this.jt=t}bt(){this.ft=!0}gt(){return this.ft&&(this.Mt(),this.ft=!1),this.Wt}Mt(){const t=this.jt.yt(),i=f(this.jt.Ht()),n=i.$t().W().crosshair,s=this.Ft;if(2===n.mode)return s.Lt.yt=!1,void(s.It.yt=!1);s.Lt.yt=t&&this.jt.Ut(i),s.It.yt=t&&this.jt.qt(),s.Lt.et=n.horzLine.width,s.Lt.Nt=n.horzLine.style,s.Lt.O=n.horzLine.color,s.It.et=n.vertLine.width,s.It.Nt=n.vertLine.style,s.It.O=n.vertLine.color,s.nt=this.jt.Yt(),s.st=this.jt.Zt()}}function q(t,i,n,s,e,r){t.fillRect(i+r,n,s-2*r,r),t.fillRect(i+r,n+e-r,s-2*r,r),t.fillRect(i,n,r,e),t.fillRect(i+s-r,n,r,e)}function Y(t,i,n,s,e,r){t.save(),t.globalCompositeOperation=\"copy\",t.fillStyle=r,t.fillRect(i,n,s,e),t.restore()}function Z(t,i,n,s,e,r){t.beginPath(),t.roundRect?t.roundRect(i,n,s,e,r):(t.lineTo(i+s-r[1],n),0!==r[1]&&t.arcTo(i+s,n,i+s,n+r[1],r[1]),t.lineTo(i+s,n+e-r[2]),0!==r[2]&&t.arcTo(i+s,n+e,i+s-r[2],n+e,r[2]),t.lineTo(i+r[3],n+e),0!==r[3]&&t.arcTo(i,n+e,i,n+e-r[3],r[3]),t.lineTo(i,n+r[0]),0!==r[0]&&t.arcTo(i,n,i+r[0],n,r[0]))}function X(t,i,n,s,e,r,h=0,l=[0,0,0,0],a=\"\"){if(t.save(),!h||!a||a===r)return Z(t,i,n,s,e,l),t.fillStyle=r,t.fill(),void t.restore();const o=h/2;var _;Z(t,i+o,n+o,s-h,e-h,(_=-o,l.map((t=>0===t?t:t+_)))),\"transparent\"!==r&&(t.fillStyle=r,t.fill()),\"transparent\"!==a&&(t.lineWidth=h,t.strokeStyle=a,t.closePath(),t.stroke()),t.restore()}function K(t,i,n,s,e,r,h){t.save(),t.globalCompositeOperation=\"copy\";const l=t.createLinearGradient(0,0,0,e);l.addColorStop(0,r),l.addColorStop(1,h),t.fillStyle=l,t.fillRect(i,n,s,e),t.restore()}class G{constructor(t,i){this.J(t,i)}J(t,i){this.Et=t,this.Xt=i}At(t,i){return this.Et.yt?t.P+t.L+t.V:0}X(t,i,n,s){if(!this.Et.yt||0===this.Et.Kt.length)return;const e=this.Et.O,r=this.Xt.t,h=t.useBitmapCoordinateSpace((t=>{const h=t.context;h.font=i.R;const l=this.Gt(t,i,n,s),a=l.Jt;return l.Qt?X(h,a.ti,a.ii,a.ni,a.si,r,a.ei,[a.ht,0,0,a.ht],r):X(h,a.ri,a.ii,a.ni,a.si,r,a.ei,[0,a.ht,a.ht,0],r),this.Et.hi&&(h.fillStyle=e,h.fillRect(a.ri,a.li,a.ai-a.ri,a.oi)),this.Et._i&&(h.fillStyle=i.B,h.fillRect(l.Qt?a.ui-a.ei:0,a.ii,a.ei,a.ci-a.ii)),l}));t.useMediaCoordinateSpace((({context:t})=>{const n=h.di;t.font=i.R,t.textAlign=h.Qt?\"right\":\"left\",t.textBaseline=\"middle\",t.fillStyle=e,t.fillText(this.Et.Kt,n.fi,(n.ii+n.ci)/2+n.pi)}))}Gt(t,i,n,s){var e;const{context:r,bitmapSize:h,mediaSize:l,horizontalPixelRatio:a,verticalPixelRatio:o}=t,_=this.Et.hi||!this.Et.mi?i.T:0,u=this.Et.bi?i.C:0,c=i.L+this.Xt.wi,d=i.V+this.Xt.gi,f=i.A,v=i.I,p=this.Et.Kt,m=i.P,b=n.Mi(r,p),w=Math.ceil(n.xi(r,p)),g=m+c+d,M=i.C+f+v+w+_,x=Math.max(1,Math.floor(o));let S=Math.round(g*o);S%2!=x%2&&(S+=1);const k=u>0?Math.max(1,Math.floor(u*a)):0,y=Math.round(M*a),C=Math.round(_*a),T=null!==(e=this.Xt.Si)&&void 0!==e?e:this.Xt.ki,P=Math.round(T*o)-Math.floor(.5*o),R=Math.floor(P+x/2-S/2),D=R+S,O=\"right\"===s,B=O?l.width-u:u,V=O?h.width-k:k;let A,z,E;return O?(A=V-y,z=V-C,E=B-_-f-u):(A=V+y,z=V+C,E=B+_+f),{Qt:O,Jt:{ii:R,li:P,ci:D,ni:y,si:S,ht:2*a,ei:k,ti:A,ri:V,ai:z,oi:x,ui:h.width},di:{ii:R/o,ci:D/o,fi:E,pi:b}}}}class J{constructor(t){this.yi={ki:0,t:\"#000\",gi:0,wi:0},this.Ci={Kt:\"\",yt:!1,hi:!0,mi:!1,Bt:\"\",O:\"#FFF\",_i:!1,bi:!1},this.Ti={Kt:\"\",yt:!1,hi:!1,mi:!0,Bt:\"\",O:\"#FFF\",_i:!0,bi:!0},this.ft=!0,this.Pi=new(t||G)(this.Ci,this.yi),this.Ri=new(t||G)(this.Ti,this.yi)}Kt(){return this.Di(),this.Ci.Kt}ki(){return this.Di(),this.yi.ki}bt(){this.ft=!0}At(t,i=!1){return Math.max(this.Pi.At(t,i),this.Ri.At(t,i))}Oi(){return this.yi.Si||0}Bi(t){this.yi.Si=t}Vi(){return this.Di(),this.Ci.yt||this.Ti.yt}Ai(){return this.Di(),this.Ci.yt}gt(t){return this.Di(),this.Ci.hi=this.Ci.hi&&t.W().ticksVisible,this.Ti.hi=this.Ti.hi&&t.W().ticksVisible,this.Pi.J(this.Ci,this.yi),this.Ri.J(this.Ti,this.yi),this.Pi}zi(){return this.Di(),this.Pi.J(this.Ci,this.yi),this.Ri.J(this.Ti,this.yi),this.Ri}Di(){this.ft&&(this.Ci.hi=!0,this.Ti.hi=!1,this.Ei(this.Ci,this.Ti,this.yi))}}class Q extends J{constructor(t,i,n){super(),this.jt=t,this.Ii=i,this.Li=n}Ei(t,i,n){if(t.yt=!1,2===this.jt.W().mode)return;const s=this.jt.W().horzLine;if(!s.labelVisible)return;const e=this.Ii.Ct();if(!this.jt.yt()||this.Ii.Ni()||null===e)return;const r=y(s.labelBackgroundColor);n.t=r.t,t.O=r.i;const h=2/12*this.Ii.P();n.wi=h,n.gi=h;const l=this.Li(this.Ii);n.ki=l.ki,t.Kt=this.Ii.Fi(l._t,e),t.yt=!0}}const tt=/[1-9]/g;class it{constructor(){this.Et=null}J(t){this.Et=t}X(t,i){if(null===this.Et||!1===this.Et.yt||0===this.Et.Kt.length)return;const n=t.useMediaCoordinateSpace((({context:t})=>(t.font=i.R,Math.round(i.Wi.xi(t,f(this.Et).Kt,tt)))));if(n<=0)return;const s=i.ji,e=n+2*s,r=e/2,h=this.Et.Hi;let l=this.Et.ki,a=Math.floor(l-r)+.5;a<0?(l+=Math.abs(0-a),a=Math.floor(l-r)+.5):a+e>h&&(l-=Math.abs(h-(a+e)),a=Math.floor(l-r)+.5);const o=a+e,_=Math.ceil(0+i.C+i.T+i.L+i.P+i.V);t.useBitmapCoordinateSpace((({context:t,horizontalPixelRatio:n,verticalPixelRatio:s})=>{const e=f(this.Et);t.fillStyle=e.t;const r=Math.round(a*n),h=Math.round(0*s),l=Math.round(o*n),u=Math.round(_*s),c=Math.round(2*n);if(t.beginPath(),t.moveTo(r,h),t.lineTo(r,u-c),t.arcTo(r,u,r+c,u,c),t.lineTo(l-c,u),t.arcTo(l,u,l,u-c,c),t.lineTo(l,h),t.fill(),e.hi){const r=Math.round(e.ki*n),l=h,a=Math.round((l+i.T)*s);t.fillStyle=e.O;const o=Math.max(1,Math.floor(n)),_=Math.floor(.5*n);t.fillRect(r-_,l,o,a-l)}})),t.useMediaCoordinateSpace((({context:t})=>{const n=f(this.Et),e=0+i.C+i.T+i.L+i.P/2;t.font=i.R,t.textAlign=\"left\",t.textBaseline=\"middle\",t.fillStyle=n.O;const r=i.Wi.Mi(t,\"Apr0\");t.translate(a+s,e+r),t.fillText(n.Kt,0,0)}))}}class nt{constructor(t,i,n){this.ft=!0,this.Wt=new it,this.Ft={yt:!1,t:\"#4c525e\",O:\"white\",Kt:\"\",Hi:0,ki:NaN,hi:!0},this.vt=t,this.$i=i,this.Li=n}bt(){this.ft=!0}gt(){return this.ft&&(this.Mt(),this.ft=!1),this.Wt.J(this.Ft),this.Wt}Mt(){const t=this.Ft;if(t.yt=!1,2===this.vt.W().mode)return;const i=this.vt.W().vertLine;if(!i.labelVisible)return;const n=this.$i.St();if(n.Ni())return;t.Hi=n.Hi();const s=this.Li();if(null===s)return;t.ki=s.ki;const e=n.Ui(this.vt.xt());t.Kt=n.qi(f(e)),t.yt=!0;const r=y(i.labelBackgroundColor);t.t=r.t,t.O=r.i,t.hi=n.W().ticksVisible}}class st{constructor(){this.Yi=null,this.Zi=0}Xi(){return this.Zi}Ki(t){this.Zi=t}Dt(){return this.Yi}Gi(t){this.Yi=t}Ji(t){return[]}Qi(){return[]}yt(){return!0}}var et;!function(t){t[t.Normal=0]=\"Normal\",t[t.Magnet=1]=\"Magnet\",t[t.Hidden=2]=\"Hidden\"}(et||(et={}));class rt extends st{constructor(t,i){super(),this.tn=null,this.nn=NaN,this.sn=0,this.en=!0,this.rn=new Map,this.hn=!1,this.ln=NaN,this.an=NaN,this._n=NaN,this.un=NaN,this.$i=t,this.cn=i,this.dn=new H(t,this);this.fn=((t,i)=>n=>{const s=i(),e=t();if(n===f(this.tn).vn())return{_t:e,ki:s};{const t=f(n.Ct());return{_t:n.pn(s,t),ki:s}}})((()=>this.nn),(()=>this.an));const n=((t,i)=>()=>{const n=this.$i.St().mn(t()),s=i();return n&&Number.isFinite(s)?{ot:n,ki:s}:null})((()=>this.sn),(()=>this.Yt()));this.bn=new nt(this,t,n),this.wn=new U(this)}W(){return this.cn}gn(t,i){this._n=t,this.un=i}Mn(){this._n=NaN,this.un=NaN}xn(){return this._n}Sn(){return this.un}kn(t,i,n){this.hn||(this.hn=!0),this.en=!0,this.yn(t,i,n)}xt(){return this.sn}Yt(){return this.ln}Zt(){return this.an}yt(){return this.en}Cn(){this.en=!1,this.Tn(),this.nn=NaN,this.ln=NaN,this.an=NaN,this.tn=null,this.Mn()}Pn(t){return null!==this.tn?[this.wn,this.dn]:[]}Ut(t){return t===this.tn&&this.cn.horzLine.visible}qt(){return this.cn.vertLine.visible}Rn(t,i){this.en&&this.tn===t||this.rn.clear();const n=[];return this.tn===t&&n.push(this.Dn(this.rn,i,this.fn)),n}Qi(){return this.en?[this.bn]:[]}Ht(){return this.tn}On(){this.wn.bt(),this.rn.forEach((t=>t.bt())),this.bn.bt(),this.dn.bt()}Bn(t){return t&&!t.vn().Ni()?t.vn():null}yn(t,i,n){this.Vn(t,i,n)&&this.On()}Vn(t,i,n){const s=this.ln,e=this.an,r=this.nn,h=this.sn,l=this.tn,a=this.Bn(n);this.sn=t,this.ln=isNaN(t)?NaN:this.$i.St().zt(t),this.tn=n;const o=null!==a?a.Ct():null;return null!==a&&null!==o?(this.nn=i,this.an=a.Rt(i,o)):(this.nn=NaN,this.an=NaN),s!==this.ln||e!==this.an||h!==this.sn||r!==this.nn||l!==this.tn}Tn(){const t=this.$i.wt().map((t=>t.zn().An())).filter(V),i=0===t.length?null:Math.max(...t);this.sn=null!==i?i:NaN}Dn(t,i,n){let s=t.get(i);return void 0===s&&(s=new Q(this,i,n),t.set(i,s)),s}}function ht(t){return\"left\"===t||\"right\"===t}class lt{constructor(t){this.En=new Map,this.In=[],this.Ln=t}Nn(t,i){const n=function(t,i){return void 0===t?i:{Fn:Math.max(t.Fn,i.Fn),Wn:t.Wn||i.Wn}}(this.En.get(t),i);this.En.set(t,n)}jn(){return this.Ln}Hn(t){const i=this.En.get(t);return void 0===i?{Fn:this.Ln}:{Fn:Math.max(this.Ln,i.Fn),Wn:i.Wn}}$n(){this.Un(),this.In=[{qn:0}]}Yn(t){this.Un(),this.In=[{qn:1,Ot:t}]}Zn(t){this.Xn(),this.In.push({qn:5,Ot:t})}Un(){this.Xn(),this.In.push({qn:6})}Kn(){this.Un(),this.In=[{qn:4}]}Gn(t){this.Un(),this.In.push({qn:2,Ot:t})}Jn(t){this.Un(),this.In.push({qn:3,Ot:t})}Qn(){return this.In}ts(t){for(const i of t.In)this.ns(i);this.Ln=Math.max(this.Ln,t.Ln),t.En.forEach(((t,i)=>{this.Nn(i,t)}))}static ss(){return new lt(2)}static es(){return new lt(3)}ns(t){switch(t.qn){case 0:this.$n();break;case 1:this.Yn(t.Ot);break;case 2:this.Gn(t.Ot);break;case 3:this.Jn(t.Ot);break;case 4:this.Kn();break;case 5:this.Zn(t.Ot);break;case 6:this.Xn()}}Xn(){const t=this.In.findIndex((t=>5===t.qn));-1!==t&&this.In.splice(t,1)}}const at=\".\";function ot(t,i){if(!P(t))return\"n/a\";if(!R(i))throw new TypeError(\"invalid length\");if(i<0||i>16)throw new TypeError(\"invalid length\");if(0===i)return t.toString();return(\"0000000000000000\"+t.toString()).slice(-i)}class _t{constructor(t,i){if(i||(i=1),P(t)&&R(t)||(t=100),t<0)throw new TypeError(\"invalid base\");this.Ii=t,this.rs=i,this.hs()}format(t){const i=t<0?\"−\":\"\";return t=Math.abs(t),i+this.ls(t)}hs(){if(this._s=0,this.Ii>0&&this.rs>0){let t=this.Ii;for(;t>1;)t/=10,this._s++}}ls(t){const i=this.Ii/this.rs;let n=Math.floor(t),s=\"\";const e=void 0!==this._s?this._s:NaN;if(i>1){let r=+(Math.round(t*i)-n*i).toFixed(this._s);r>=i&&(r-=i,n+=1),s=at+ot(+r.toFixed(this._s)*this.rs,e)}else n=Math.round(n*i)/i,e>0&&(s=at+ot(0,e));return n.toFixed(0)+s}}class ut extends _t{constructor(t=100){super(t)}format(t){return`${super.format(t)}%`}}class ct{constructor(t){this.us=t}format(t){let i=\"\";return t<0&&(i=\"-\",t=-t),t<995?i+this.cs(t):t<999995?i+this.cs(t/1e3)+\"K\":t<999999995?(t=1e3*Math.round(t/1e3),i+this.cs(t/1e6)+\"M\"):(t=1e6*Math.round(t/1e6),i+this.cs(t/1e9)+\"B\")}cs(t){let i;const n=Math.pow(10,this.us);return i=(t=Math.round(t*n)/n)>=1e-15&&t<1?t.toFixed(this.us).replace(/\\.?0+$/,\"\"):String(t),i.replace(/(\\.[1-9]*)0+$/,((t,i)=>i))}}function dt(t,i,n,s,e,r,h){if(0===i.length||s.from>=i.length||s.to<=0)return;const{context:l,horizontalPixelRatio:a,verticalPixelRatio:o}=t,_=i[s.from];let u=r(t,_),c=_;if(s.to-s.from<2){const i=e/2;l.beginPath();const n={nt:_.nt-i,st:_.st},s={nt:_.nt+i,st:_.st};l.moveTo(n.nt*a,n.st*o),l.lineTo(s.nt*a,s.st*o),h(t,u,n,s)}else{const e=(i,n)=>{h(t,u,c,n),l.beginPath(),u=i,c=n};let d=c;l.beginPath(),l.moveTo(_.nt*a,_.st*o);for(let h=s.from+1;h<s.to;++h){d=i[h];const s=r(t,d);switch(n){case 0:l.lineTo(d.nt*a,d.st*o);break;case 1:l.lineTo(d.nt*a,i[h-1].st*o),s!==u&&(e(s,d),l.lineTo(d.nt*a,i[h-1].st*o)),l.lineTo(d.nt*a,d.st*o);break;case 2:{const[t,n]=mt(i,h-1,h);l.bezierCurveTo(t.nt*a,t.st*o,n.nt*a,n.st*o,d.nt*a,d.st*o);break}}1!==n&&s!==u&&(e(s,d),l.moveTo(d.nt*a,d.st*o))}(c!==d||c===d&&1===n)&&h(t,u,c,d)}}const ft=6;function vt(t,i){return{nt:t.nt-i.nt,st:t.st-i.st}}function pt(t,i){return{nt:t.nt/i,st:t.st/i}}function mt(t,i,n){const s=Math.max(0,i-1),e=Math.min(t.length-1,n+1);var r,h;return[(r=t[i],h=pt(vt(t[n],t[s]),ft),{nt:r.nt+h.nt,st:r.st+h.st}),vt(t[n],pt(vt(t[e],t[i]),ft))]}function bt(t,i,n,s,e){const{context:r,horizontalPixelRatio:h,verticalPixelRatio:l}=i;r.lineTo(e.nt*h,t*l),r.lineTo(s.nt*h,t*l),r.closePath(),r.fillStyle=n,r.fill()}class wt extends N{constructor(){super(...arguments),this.G=null}J(t){this.G=t}K(t){var i;if(null===this.G)return;const{it:n,tt:s,ds:e,et:r,Nt:h,fs:l}=this.G,a=null!==(i=this.G.vs)&&void 0!==i?i:this.G.ps?0:t.mediaSize.height;if(null===s)return;const o=t.context;o.lineCap=\"butt\",o.lineJoin=\"round\",o.lineWidth=r,_(o,h),o.lineWidth=1,dt(t,n,l,s,e,this.bs.bind(this),bt.bind(null,a))}}function gt(t,i,n){return Math.min(Math.max(t,i),n)}function Mt(t,i,n){return i-t<=n}function xt(t){const i=Math.ceil(t);return i%2==0?i-1:i}class St{ws(t,i){const n=this.gs,{Ms:s,xs:e,Ss:r,ks:h,ys:l,vs:a}=i;if(void 0===this.Cs||void 0===n||n.Ms!==s||n.xs!==e||n.Ss!==r||n.ks!==h||n.vs!==a||n.ys!==l){const n=t.context.createLinearGradient(0,0,0,l);if(n.addColorStop(0,s),null!=a){const i=gt(a*t.verticalPixelRatio/l,0,1);n.addColorStop(i,e),n.addColorStop(i,r)}n.addColorStop(1,h),this.Cs=n,this.gs=i}return this.Cs}}class kt extends wt{constructor(){super(...arguments),this.Ts=new St}bs(t,i){return this.Ts.ws(t,{Ms:i.Ps,xs:\"\",Ss:\"\",ks:i.Rs,ys:t.bitmapSize.height})}}function yt(t,i){const n=t.context;n.strokeStyle=i,n.stroke()}class Ct extends N{constructor(){super(...arguments),this.G=null}J(t){this.G=t}K(t){if(null===this.G)return;const{it:i,tt:n,ds:s,fs:e,et:r,Nt:h,Ds:l}=this.G;if(null===n)return;const a=t.context;a.lineCap=\"butt\",a.lineWidth=r*t.verticalPixelRatio,_(a,h),a.lineJoin=\"round\";const o=this.Os.bind(this);void 0!==e&&dt(t,i,e,n,s,o,yt),l&&function(t,i,n,s,e){const{horizontalPixelRatio:r,verticalPixelRatio:h,context:l}=t;let a=null;const o=Math.max(1,Math.floor(r))%2/2,_=n*h+o;for(let n=s.to-1;n>=s.from;--n){const s=i[n];if(s){const i=e(t,s);i!==a&&(l.beginPath(),null!==a&&l.fill(),l.fillStyle=i,a=i);const n=Math.round(s.nt*r)+o,u=s.st*h;l.moveTo(n,u),l.arc(n,u,_,0,2*Math.PI)}}l.fill()}(t,i,l,n,o)}}class Tt extends Ct{Os(t,i){return i.lt}}function Pt(t,i,n,s,e=0,r=i.length){let h=r-e;for(;0<h;){const r=h>>1,l=e+r;s(i[l],n)===t?(e=l+1,h-=r+1):h=r}return e}const Rt=Pt.bind(null,!0),Dt=Pt.bind(null,!1);function Ot(t,i){return t.ot<i}function Bt(t,i){return i<t.ot}function Vt(t,i,n){const s=i.Bs(),e=i.ui(),r=Rt(t,s,Ot),h=Dt(t,e,Bt);if(!n)return{from:r,to:h};let l=r,a=h;return r>0&&r<t.length&&t[r].ot>=s&&(l=r-1),h>0&&h<t.length&&t[h-1].ot<=e&&(a=h+1),{from:l,to:a}}class At{constructor(t,i,n){this.Vs=!0,this.As=!0,this.zs=!0,this.Es=[],this.Is=null,this.Ls=t,this.Ns=i,this.Fs=n}bt(t){this.Vs=!0,\"data\"===t&&(this.As=!0),\"options\"===t&&(this.zs=!0)}gt(){return this.Ls.yt()?(this.Ws(),null===this.Is?null:this.js):null}Hs(){this.Es=this.Es.map((t=>Object.assign(Object.assign({},t),this.Ls.Us().$s(t.ot))))}qs(){this.Is=null}Ws(){this.As&&(this.Ys(),this.As=!1),this.zs&&(this.Hs(),this.zs=!1),this.Vs&&(this.Zs(),this.Vs=!1)}Zs(){const t=this.Ls.Dt(),i=this.Ns.St();if(this.qs(),i.Ni()||t.Ni())return;const n=i.Xs();if(null===n)return;if(0===this.Ls.zn().Ks())return;const s=this.Ls.Ct();null!==s&&(this.Is=Vt(this.Es,n,this.Fs),this.Gs(t,i,s.Ot),this.Js())}}class zt extends At{constructor(t,i){super(t,i,!0)}Gs(t,i,n){i.Qs(this.Es,A(this.Is)),t.te(this.Es,n,A(this.Is))}ie(t,i){return{ot:t,_t:i,nt:NaN,st:NaN}}Ys(){const t=this.Ls.Us();this.Es=this.Ls.zn().ne().map((i=>{const n=i.Ot[3];return this.se(i.ee,n,t)}))}}class Et extends zt{constructor(t,i){super(t,i),this.js=new L,this.re=new kt,this.he=new Tt,this.js.Z([this.re,this.he])}se(t,i,n){return Object.assign(Object.assign({},this.ie(t,i)),n.$s(t))}Js(){const t=this.Ls.W();this.re.J({fs:t.lineType,it:this.Es,Nt:t.lineStyle,et:t.lineWidth,vs:null,ps:t.invertFilledArea,tt:this.Is,ds:this.Ns.St().le()}),this.he.J({fs:t.lineVisible?t.lineType:void 0,it:this.Es,Nt:t.lineStyle,et:t.lineWidth,tt:this.Is,ds:this.Ns.St().le(),Ds:t.pointMarkersVisible?t.pointMarkersRadius||t.lineWidth/2+2:void 0})}}class It extends N{constructor(){super(...arguments),this.Et=null,this.ae=0,this.oe=0}J(t){this.Et=t}K({context:t,horizontalPixelRatio:i,verticalPixelRatio:n}){if(null===this.Et||0===this.Et.zn.length||null===this.Et.tt)return;if(this.ae=this._e(i),this.ae>=2){Math.max(1,Math.floor(i))%2!=this.ae%2&&this.ae--}this.oe=this.Et.ue?Math.min(this.ae,Math.floor(i)):this.ae;let s=null;const e=this.oe<=this.ae&&this.Et.le>=Math.floor(1.5*i);for(let r=this.Et.tt.from;r<this.Et.tt.to;++r){const h=this.Et.zn[r];s!==h.ce&&(t.fillStyle=h.ce,s=h.ce);const l=Math.floor(.5*this.oe),a=Math.round(h.nt*i),o=a-l,_=this.oe,u=o+_-1,c=Math.min(h.de,h.fe),d=Math.max(h.de,h.fe),f=Math.round(c*n)-l,v=Math.round(d*n)+l,p=Math.max(v-f,this.oe);t.fillRect(o,f,_,p);const m=Math.ceil(1.5*this.ae);if(e){if(this.Et.ve){const i=a-m;let s=Math.max(f,Math.round(h.pe*n)-l),e=s+_-1;e>f+p-1&&(e=f+p-1,s=e-_+1),t.fillRect(i,s,o-i,e-s+1)}const i=a+m;let s=Math.max(f,Math.round(h.me*n)-l),e=s+_-1;e>f+p-1&&(e=f+p-1,s=e-_+1),t.fillRect(u+1,s,i-u,e-s+1)}}}_e(t){const i=Math.floor(t);return Math.max(i,Math.floor(function(t,i){return Math.floor(.3*t*i)}(f(this.Et).le,t)))}}class Lt extends At{constructor(t,i){super(t,i,!1)}Gs(t,i,n){i.Qs(this.Es,A(this.Is)),t.be(this.Es,n,A(this.Is))}we(t,i,n){return{ot:t,ge:i.Ot[0],Me:i.Ot[1],xe:i.Ot[2],Se:i.Ot[3],nt:NaN,pe:NaN,de:NaN,fe:NaN,me:NaN}}Ys(){const t=this.Ls.Us();this.Es=this.Ls.zn().ne().map((i=>this.se(i.ee,i,t)))}}class Nt extends Lt{constructor(){super(...arguments),this.js=new It}se(t,i,n){return Object.assign(Object.assign({},this.we(t,i,n)),n.$s(t))}Js(){const t=this.Ls.W();this.js.J({zn:this.Es,le:this.Ns.St().le(),ve:t.openVisible,ue:t.thinBars,tt:this.Is})}}class Ft extends wt{constructor(){super(...arguments),this.Ts=new St}bs(t,i){const n=this.G;return this.Ts.ws(t,{Ms:i.ke,xs:i.ye,Ss:i.Ce,ks:i.Te,ys:t.bitmapSize.height,vs:n.vs})}}class Wt extends Ct{constructor(){super(...arguments),this.Pe=new St}Os(t,i){const n=this.G;return this.Pe.ws(t,{Ms:i.Re,xs:i.Re,Ss:i.De,ks:i.De,ys:t.bitmapSize.height,vs:n.vs})}}class jt extends zt{constructor(t,i){super(t,i),this.js=new L,this.Oe=new Ft,this.Be=new Wt,this.js.Z([this.Oe,this.Be])}se(t,i,n){return Object.assign(Object.assign({},this.ie(t,i)),n.$s(t))}Js(){const t=this.Ls.Ct();if(null===t)return;const i=this.Ls.W(),n=this.Ls.Dt().Rt(i.baseValue.price,t.Ot),s=this.Ns.St().le();this.Oe.J({it:this.Es,et:i.lineWidth,Nt:i.lineStyle,fs:i.lineType,vs:n,ps:!1,tt:this.Is,ds:s}),this.Be.J({it:this.Es,et:i.lineWidth,Nt:i.lineStyle,fs:i.lineVisible?i.lineType:void 0,Ds:i.pointMarkersVisible?i.pointMarkersRadius||i.lineWidth/2+2:void 0,vs:n,tt:this.Is,ds:s})}}class Ht extends N{constructor(){super(...arguments),this.Et=null,this.ae=0}J(t){this.Et=t}K(t){if(null===this.Et||0===this.Et.zn.length||null===this.Et.tt)return;const{horizontalPixelRatio:i}=t;if(this.ae=function(t,i){if(t>=2.5&&t<=4)return Math.floor(3*i);const n=1-.2*Math.atan(Math.max(4,t)-4)/(.5*Math.PI),s=Math.floor(t*n*i),e=Math.floor(t*i),r=Math.min(s,e);return Math.max(Math.floor(i),r)}(this.Et.le,i),this.ae>=2){Math.floor(i)%2!=this.ae%2&&this.ae--}const n=this.Et.zn;this.Et.Ve&&this.Ae(t,n,this.Et.tt),this.Et._i&&this.ze(t,n,this.Et.tt);const s=this.Ee(i);(!this.Et._i||this.ae>2*s)&&this.Ie(t,n,this.Et.tt)}Ae(t,i,n){if(null===this.Et)return;const{context:s,horizontalPixelRatio:e,verticalPixelRatio:r}=t;let h=\"\",l=Math.min(Math.floor(e),Math.floor(this.Et.le*e));l=Math.max(Math.floor(e),Math.min(l,this.ae));const a=Math.floor(.5*l);let o=null;for(let t=n.from;t<n.to;t++){const n=i[t];n.Le!==h&&(s.fillStyle=n.Le,h=n.Le);const _=Math.round(Math.min(n.pe,n.me)*r),u=Math.round(Math.max(n.pe,n.me)*r),c=Math.round(n.de*r),d=Math.round(n.fe*r);let f=Math.round(e*n.nt)-a;const v=f+l-1;null!==o&&(f=Math.max(o+1,f),f=Math.min(f,v));const p=v-f+1;s.fillRect(f,c,p,_-c),s.fillRect(f,u+1,p,d-u),o=v}}Ee(t){let i=Math.floor(1*t);this.ae<=2*i&&(i=Math.floor(.5*(this.ae-1)));const n=Math.max(Math.floor(t),i);return this.ae<=2*n?Math.max(Math.floor(t),Math.floor(1*t)):n}ze(t,i,n){if(null===this.Et)return;const{context:s,horizontalPixelRatio:e,verticalPixelRatio:r}=t;let h=\"\";const l=this.Ee(e);let a=null;for(let t=n.from;t<n.to;t++){const n=i[t];n.Ne!==h&&(s.fillStyle=n.Ne,h=n.Ne);let o=Math.round(n.nt*e)-Math.floor(.5*this.ae);const _=o+this.ae-1,u=Math.round(Math.min(n.pe,n.me)*r),c=Math.round(Math.max(n.pe,n.me)*r);if(null!==a&&(o=Math.max(a+1,o),o=Math.min(o,_)),this.Et.le*e>2*l)q(s,o,u,_-o+1,c-u+1,l);else{const t=_-o+1;s.fillRect(o,u,t,c-u+1)}a=_}}Ie(t,i,n){if(null===this.Et)return;const{context:s,horizontalPixelRatio:e,verticalPixelRatio:r}=t;let h=\"\";const l=this.Ee(e);for(let t=n.from;t<n.to;t++){const n=i[t];let a=Math.round(Math.min(n.pe,n.me)*r),o=Math.round(Math.max(n.pe,n.me)*r),_=Math.round(n.nt*e)-Math.floor(.5*this.ae),u=_+this.ae-1;if(n.ce!==h){const t=n.ce;s.fillStyle=t,h=t}this.Et._i&&(_+=l,a+=l,u-=l,o-=l),a>o||s.fillRect(_,a,u-_+1,o-a+1)}}}class $t extends Lt{constructor(){super(...arguments),this.js=new Ht}se(t,i,n){return Object.assign(Object.assign({},this.we(t,i,n)),n.$s(t))}Js(){const t=this.Ls.W();this.js.J({zn:this.Es,le:this.Ns.St().le(),Ve:t.wickVisible,_i:t.borderVisible,tt:this.Is})}}class Ut{constructor(t,i){this.Fe=t,this.Ii=i}X(t,i,n){this.Fe.draw(t,this.Ii,i,n)}}class qt extends At{constructor(t,i,n){super(t,i,!1),this.wn=n,this.js=new Ut(this.wn.renderer(),(i=>{const n=t.Ct();return null===n?null:t.Dt().Rt(i,n.Ot)}))}We(t){return this.wn.priceValueBuilder(t)}je(t){return this.wn.isWhitespace(t)}Ys(){const t=this.Ls.Us();this.Es=this.Ls.zn().ne().map((i=>Object.assign(Object.assign({ot:i.ee,nt:NaN},t.$s(i.ee)),{He:i.$e})))}Gs(t,i){i.Qs(this.Es,A(this.Is))}Js(){this.wn.update({bars:this.Es.map(Yt),barSpacing:this.Ns.St().le(),visibleRange:this.Is},this.Ls.W())}}function Yt(t){return{x:t.nt,time:t.ot,originalData:t.He,barColor:t.ce}}class Zt extends N{constructor(){super(...arguments),this.Et=null,this.Ue=[]}J(t){this.Et=t,this.Ue=[]}K({context:t,horizontalPixelRatio:i,verticalPixelRatio:n}){if(null===this.Et||0===this.Et.it.length||null===this.Et.tt)return;this.Ue.length||this.qe(i);const s=Math.max(1,Math.floor(n)),e=Math.round(this.Et.Ye*n)-Math.floor(s/2),r=e+s;for(let i=this.Et.tt.from;i<this.Et.tt.to;i++){const h=this.Et.it[i],l=this.Ue[i-this.Et.tt.from],a=Math.round(h.st*n);let o,_;t.fillStyle=h.ce,a<=e?(o=a,_=r):(o=e,_=a-Math.floor(s/2)+s),t.fillRect(l.Bs,o,l.ui-l.Bs+1,_-o)}}qe(t){if(null===this.Et||0===this.Et.it.length||null===this.Et.tt)return void(this.Ue=[]);const i=Math.ceil(this.Et.le*t)<=1?0:Math.max(1,Math.floor(t)),n=Math.round(this.Et.le*t)-i;this.Ue=new Array(this.Et.tt.to-this.Et.tt.from);for(let i=this.Et.tt.from;i<this.Et.tt.to;i++){const s=this.Et.it[i],e=Math.round(s.nt*t);let r,h;if(n%2){const t=(n-1)/2;r=e-t,h=e+t}else{const t=n/2;r=e-t,h=e+t-1}this.Ue[i-this.Et.tt.from]={Bs:r,ui:h,Ze:e,Xe:s.nt*t,ot:s.ot}}for(let t=this.Et.tt.from+1;t<this.Et.tt.to;t++){const n=this.Ue[t-this.Et.tt.from],s=this.Ue[t-this.Et.tt.from-1];n.ot===s.ot+1&&(n.Bs-s.ui!==i+1&&(s.Ze>s.Xe?s.ui=n.Bs-i-1:n.Bs=s.ui+i+1))}let s=Math.ceil(this.Et.le*t);for(let t=this.Et.tt.from;t<this.Et.tt.to;t++){const i=this.Ue[t-this.Et.tt.from];i.ui<i.Bs&&(i.ui=i.Bs);const n=i.ui-i.Bs+1;s=Math.min(n,s)}if(i>0&&s<4)for(let t=this.Et.tt.from;t<this.Et.tt.to;t++){const i=this.Ue[t-this.Et.tt.from];i.ui-i.Bs+1>s&&(i.Ze>i.Xe?i.ui-=1:i.Bs+=1)}}}class Xt extends zt{constructor(){super(...arguments),this.js=new Zt}se(t,i,n){return Object.assign(Object.assign({},this.ie(t,i)),n.$s(t))}Js(){const t={it:this.Es,le:this.Ns.St().le(),tt:this.Is,Ye:this.Ls.Dt().Rt(this.Ls.W().base,f(this.Ls.Ct()).Ot)};this.js.J(t)}}class Kt extends zt{constructor(){super(...arguments),this.js=new Tt}se(t,i,n){return Object.assign(Object.assign({},this.ie(t,i)),n.$s(t))}Js(){const t=this.Ls.W(),i={it:this.Es,Nt:t.lineStyle,fs:t.lineVisible?t.lineType:void 0,et:t.lineWidth,Ds:t.pointMarkersVisible?t.pointMarkersRadius||t.lineWidth/2+2:void 0,tt:this.Is,ds:this.Ns.St().le()};this.js.J(i)}}const Gt=/[2-9]/g;class Jt{constructor(t=50){this.Ke=0,this.Ge=1,this.Je=1,this.Qe={},this.tr=new Map,this.ir=t}nr(){this.Ke=0,this.tr.clear(),this.Ge=1,this.Je=1,this.Qe={}}xi(t,i,n){return this.sr(t,i,n).width}Mi(t,i,n){const s=this.sr(t,i,n);return((s.actualBoundingBoxAscent||0)-(s.actualBoundingBoxDescent||0))/2}sr(t,i,n){const s=n||Gt,e=String(i).replace(s,\"0\");if(this.tr.has(e))return d(this.tr.get(e)).er;if(this.Ke===this.ir){const t=this.Qe[this.Je];delete this.Qe[this.Je],this.tr.delete(t),this.Je++,this.Ke--}t.save(),t.textBaseline=\"middle\";const r=t.measureText(e);return t.restore(),0===r.width&&i.length||(this.tr.set(e,{er:r,rr:this.Ge}),this.Qe[this.Ge]=e,this.Ke++,this.Ge++),r}}class Qt{constructor(t){this.hr=null,this.k=null,this.lr=\"right\",this.ar=t}_r(t,i,n){this.hr=t,this.k=i,this.lr=n}X(t){null!==this.k&&null!==this.hr&&this.hr.X(t,this.k,this.ar,this.lr)}}class ti{constructor(t,i,n){this.ur=t,this.ar=new Jt(50),this.cr=i,this.F=n,this.j=-1,this.Wt=new Qt(this.ar)}gt(){const t=this.F.dr(this.cr);if(null===t)return null;const i=t.vr(this.cr)?t.pr():this.cr.Dt();if(null===i)return null;const n=t.mr(i);if(\"overlay\"===n)return null;const s=this.F.br();return s.P!==this.j&&(this.j=s.P,this.ar.nr()),this.Wt._r(this.ur.zi(),s,n),this.Wt}}class ii extends N{constructor(){super(...arguments),this.Et=null}J(t){this.Et=t}wr(t,i){var n;if(!(null===(n=this.Et)||void 0===n?void 0:n.yt))return null;const{st:s,et:e,gr:r}=this.Et;return i>=s-e-7&&i<=s+e+7?{Mr:this.Et,gr:r}:null}K({context:t,bitmapSize:i,horizontalPixelRatio:n,verticalPixelRatio:s}){if(null===this.Et)return;if(!1===this.Et.yt)return;const e=Math.round(this.Et.st*s);e<0||e>i.height||(t.lineCap=\"butt\",t.strokeStyle=this.Et.O,t.lineWidth=Math.floor(this.Et.et*n),_(t,this.Et.Nt),u(t,e,0,i.width))}}class ni{constructor(t){this.Sr={st:0,O:\"rgba(0, 0, 0, 0)\",et:1,Nt:0,yt:!1},this.kr=new ii,this.ft=!0,this.Ls=t,this.Ns=t.$t(),this.kr.J(this.Sr)}bt(){this.ft=!0}gt(){return this.Ls.yt()?(this.ft&&(this.yr(),this.ft=!1),this.kr):null}}class si extends ni{constructor(t){super(t)}yr(){this.Sr.yt=!1;const t=this.Ls.Dt(),i=t.Cr().Cr;if(2!==i&&3!==i)return;const n=this.Ls.W();if(!n.baseLineVisible||!this.Ls.yt())return;const s=this.Ls.Ct();null!==s&&(this.Sr.yt=!0,this.Sr.st=t.Rt(s.Ot,s.Ot),this.Sr.O=n.baseLineColor,this.Sr.et=n.baseLineWidth,this.Sr.Nt=n.baseLineStyle)}}class ei extends N{constructor(){super(...arguments),this.Et=null}J(t){this.Et=t}$e(){return this.Et}K({context:t,horizontalPixelRatio:i,verticalPixelRatio:n}){const s=this.Et;if(null===s)return;const e=Math.max(1,Math.floor(i)),r=e%2/2,h=Math.round(s.Xe.x*i)+r,l=s.Xe.y*n;t.fillStyle=s.Tr,t.beginPath();const a=Math.max(2,1.5*s.Pr)*i;t.arc(h,l,a,0,2*Math.PI,!1),t.fill(),t.fillStyle=s.Rr,t.beginPath(),t.arc(h,l,s.ht*i,0,2*Math.PI,!1),t.fill(),t.lineWidth=e,t.strokeStyle=s.Dr,t.beginPath(),t.arc(h,l,s.ht*i+e/2,0,2*Math.PI,!1),t.stroke()}}const ri=[{Or:0,Br:.25,Vr:4,Ar:10,zr:.25,Er:0,Ir:.4,Lr:.8},{Or:.25,Br:.525,Vr:10,Ar:14,zr:0,Er:0,Ir:.8,Lr:0},{Or:.525,Br:1,Vr:14,Ar:14,zr:0,Er:0,Ir:0,Lr:0}];function hi(t,i,n,s){return function(t,i){if(\"transparent\"===t)return t;const n=S(t),s=n[3];return`rgba(${n[0]}, ${n[1]}, ${n[2]}, ${i*s})`}(t,n+(s-n)*i)}function li(t,i){const n=t%2600/2600;let s;for(const t of ri)if(n>=t.Or&&n<=t.Br){s=t;break}c(void 0!==s,\"Last price animation internal logic error\");const e=(n-s.Or)/(s.Br-s.Or);return{Rr:hi(i,e,s.zr,s.Er),Dr:hi(i,e,s.Ir,s.Lr),ht:(r=e,h=s.Vr,l=s.Ar,h+(l-h)*r)};var r,h,l}class ai{constructor(t){this.Wt=new ei,this.ft=!0,this.Nr=!0,this.Fr=performance.now(),this.Wr=this.Fr-1,this.jr=t}Hr(){this.Wr=this.Fr-1,this.bt()}$r(){if(this.bt(),2===this.jr.W().lastPriceAnimation){const t=performance.now(),i=this.Wr-t;if(i>0)return void(i<650&&(this.Wr+=2600));this.Fr=t,this.Wr=t+2600}}bt(){this.ft=!0}Ur(){this.Nr=!0}yt(){return 0!==this.jr.W().lastPriceAnimation}qr(){switch(this.jr.W().lastPriceAnimation){case 0:return!1;case 1:return!0;case 2:return performance.now()<=this.Wr}}gt(){return this.ft?(this.Mt(),this.ft=!1,this.Nr=!1):this.Nr&&(this.Yr(),this.Nr=!1),this.Wt}Mt(){this.Wt.J(null);const t=this.jr.$t().St(),i=t.Xs(),n=this.jr.Ct();if(null===i||null===n)return;const s=this.jr.Zr(!0);if(s.Xr||!i.Kr(s.ee))return;const e={x:t.zt(s.ee),y:this.jr.Dt().Rt(s._t,n.Ot)},r=s.O,h=this.jr.W().lineWidth,l=li(this.Gr(),r);this.Wt.J({Tr:r,Pr:h,Rr:l.Rr,Dr:l.Dr,ht:l.ht,Xe:e})}Yr(){const t=this.Wt.$e();if(null!==t){const i=li(this.Gr(),t.Tr);t.Rr=i.Rr,t.Dr=i.Dr,t.ht=i.ht}}Gr(){return this.qr()?performance.now()-this.Fr:2599}}function oi(t,i){return xt(Math.min(Math.max(t,12),30)*i)}function _i(t,i){switch(t){case\"arrowDown\":case\"arrowUp\":return oi(i,1);case\"circle\":return oi(i,.8);case\"square\":return oi(i,.7)}}function ui(t){return function(t){const i=Math.ceil(t);return i%2!=0?i-1:i}(oi(t,1))}function ci(t){return Math.max(oi(t,.1),3)}function di(t,i,n){return i?t:n?Math.ceil(t/2):0}function fi(t,i,n,s,e){const r=_i(\"square\",n),h=(r-1)/2,l=t-h,a=i-h;return s>=l&&s<=l+r&&e>=a&&e<=a+r}function vi(t,i,n,s){const e=(_i(\"arrowUp\",s)-1)/2*n.Jr,r=(xt(s/2)-1)/2*n.Jr;i.beginPath(),t?(i.moveTo(n.nt-e,n.st),i.lineTo(n.nt,n.st-e),i.lineTo(n.nt+e,n.st),i.lineTo(n.nt+r,n.st),i.lineTo(n.nt+r,n.st+e),i.lineTo(n.nt-r,n.st+e),i.lineTo(n.nt-r,n.st)):(i.moveTo(n.nt-e,n.st),i.lineTo(n.nt,n.st+e),i.lineTo(n.nt+e,n.st),i.lineTo(n.nt+r,n.st),i.lineTo(n.nt+r,n.st-e),i.lineTo(n.nt-r,n.st-e),i.lineTo(n.nt-r,n.st)),i.fill()}function pi(t,i,n,s,e,r){return fi(i,n,s,e,r)}class mi extends N{constructor(){super(...arguments),this.Et=null,this.ar=new Jt,this.j=-1,this.H=\"\",this.Qr=\"\"}J(t){this.Et=t}_r(t,i){this.j===t&&this.H===i||(this.j=t,this.H=i,this.Qr=E(t,i),this.ar.nr())}wr(t,i){if(null===this.Et||null===this.Et.tt)return null;for(let n=this.Et.tt.from;n<this.Et.tt.to;n++){const s=this.Et.it[n];if(wi(s,t,i))return{Mr:s.th,gr:s.gr}}return null}K({context:t,horizontalPixelRatio:i,verticalPixelRatio:n},s,e){if(null!==this.Et&&null!==this.Et.tt){t.textBaseline=\"middle\",t.font=this.Qr;for(let s=this.Et.tt.from;s<this.Et.tt.to;s++){const e=this.Et.it[s];void 0!==e.Kt&&(e.Kt.Hi=this.ar.xi(t,e.Kt.ih),e.Kt.At=this.j,e.Kt.nt=e.nt-e.Kt.Hi/2),bi(e,t,i,n)}}}}function bi(t,i,n,s){i.fillStyle=t.O,void 0!==t.Kt&&function(t,i,n,s,e,r){t.save(),t.scale(e,r),t.fillText(i,n,s),t.restore()}(i,t.Kt.ih,t.Kt.nt,t.Kt.st,n,s),function(t,i,n){if(0===t.Ks)return;switch(t.nh){case\"arrowDown\":return void vi(!1,i,n,t.Ks);case\"arrowUp\":return void vi(!0,i,n,t.Ks);case\"circle\":return void function(t,i,n){const s=(_i(\"circle\",n)-1)/2;t.beginPath(),t.arc(i.nt,i.st,s*i.Jr,0,2*Math.PI,!1),t.fill()}(i,n,t.Ks);case\"square\":return void function(t,i,n){const s=_i(\"square\",n),e=(s-1)*i.Jr/2,r=i.nt-e,h=i.st-e;t.fillRect(r,h,s*i.Jr,s*i.Jr)}(i,n,t.Ks)}t.nh}(t,i,function(t,i,n){const s=Math.max(1,Math.floor(i))%2/2;return{nt:Math.round(t.nt*i)+s,st:t.st*n,Jr:i}}(t,n,s))}function wi(t,i,n){return!(void 0===t.Kt||!function(t,i,n,s,e,r){const h=s/2;return e>=t&&e<=t+n&&r>=i-h&&r<=i+h}(t.Kt.nt,t.Kt.st,t.Kt.Hi,t.Kt.At,i,n))||function(t,i,n){if(0===t.Ks)return!1;switch(t.nh){case\"arrowDown\":case\"arrowUp\":return pi(0,t.nt,t.st,t.Ks,i,n);case\"circle\":return function(t,i,n,s,e){const r=2+_i(\"circle\",n)/2,h=t-s,l=i-e;return Math.sqrt(h*h+l*l)<=r}(t.nt,t.st,t.Ks,i,n);case\"square\":return fi(t.nt,t.st,t.Ks,i,n)}}(t,i,n)}function gi(t,i,n,s,e,r,h,l,a){const o=P(n)?n:n.Se,_=P(n)?n:n.Me,u=P(n)?n:n.xe,c=P(i.size)?Math.max(i.size,0):1,d=ui(l.le())*c,f=d/2;switch(t.Ks=d,i.position){case\"inBar\":return t.st=h.Rt(o,a),void(void 0!==t.Kt&&(t.Kt.st=t.st+f+r+.6*e));case\"aboveBar\":return t.st=h.Rt(_,a)-f-s.sh,void 0!==t.Kt&&(t.Kt.st=t.st-f-.6*e,s.sh+=1.2*e),void(s.sh+=d+r);case\"belowBar\":return t.st=h.Rt(u,a)+f+s.eh,void 0!==t.Kt&&(t.Kt.st=t.st+f+r+.6*e,s.eh+=1.2*e),void(s.eh+=d+r)}i.position}class Mi{constructor(t,i){this.ft=!0,this.rh=!0,this.hh=!0,this.ah=null,this.oh=null,this.Wt=new mi,this.jr=t,this.$i=i,this.Et={it:[],tt:null}}bt(t){this.ft=!0,this.hh=!0,\"data\"===t&&(this.rh=!0,this.oh=null)}gt(t){if(!this.jr.yt())return null;this.ft&&this._h();const i=this.$i.W().layout;return this.Wt._r(i.fontSize,i.fontFamily),this.Wt.J(this.Et),this.Wt}uh(){if(this.hh){if(this.jr.dh().length>0){const t=this.$i.St().le(),i=ci(t),n=1.5*ui(t)+2*i,s=this.fh();this.ah={above:di(n,s.aboveBar,s.inBar),below:di(n,s.belowBar,s.inBar)}}else this.ah=null;this.hh=!1}return this.ah}fh(){return null===this.oh&&(this.oh=this.jr.dh().reduce(((t,i)=>(t[i.position]||(t[i.position]=!0),t)),{inBar:!1,aboveBar:!1,belowBar:!1})),this.oh}_h(){const t=this.jr.Dt(),i=this.$i.St(),n=this.jr.dh();this.rh&&(this.Et.it=n.map((t=>({ot:t.time,nt:0,st:0,Ks:0,nh:t.shape,O:t.color,th:t.th,gr:t.id,Kt:void 0}))),this.rh=!1);const s=this.$i.W().layout;this.Et.tt=null;const e=i.Xs();if(null===e)return;const r=this.jr.Ct();if(null===r)return;if(0===this.Et.it.length)return;let h=NaN;const l=ci(i.le()),a={sh:l,eh:l};this.Et.tt=Vt(this.Et.it,e,!0);for(let e=this.Et.tt.from;e<this.Et.tt.to;e++){const o=n[e];o.time!==h&&(a.sh=l,a.eh=l,h=o.time);const _=this.Et.it[e];_.nt=i.zt(o.time),void 0!==o.text&&o.text.length>0&&(_.Kt={ih:o.text,nt:0,st:0,Hi:0,At:0});const u=this.jr.ph(o.time);null!==u&&gi(_,o,u,a,s.fontSize,l,t,i,r.Ot)}this.ft=!1}}class xi extends ni{constructor(t){super(t)}yr(){const t=this.Sr;t.yt=!1;const i=this.Ls.W();if(!i.priceLineVisible||!this.Ls.yt())return;const n=this.Ls.Zr(0===i.priceLineSource);n.Xr||(t.yt=!0,t.st=n.ki,t.O=this.Ls.mh(n.O),t.et=i.priceLineWidth,t.Nt=i.priceLineStyle)}}class Si extends J{constructor(t){super(),this.jt=t}Ei(t,i,n){t.yt=!1,i.yt=!1;const s=this.jt;if(!s.yt())return;const e=s.W(),r=e.lastValueVisible,h=\"\"!==s.bh(),l=0===e.seriesLastValueMode,a=s.Zr(!1);if(a.Xr)return;r&&(t.Kt=this.wh(a,r,l),t.yt=0!==t.Kt.length),(h||l)&&(i.Kt=this.gh(a,r,h,l),i.yt=i.Kt.length>0);const o=s.mh(a.O),_=y(o);n.t=_.t,n.ki=a.ki,i.Bt=s.$t().Vt(a.ki/s.Dt().At()),t.Bt=o,t.O=_.i,i.O=_.i}gh(t,i,n,s){let e=\"\";const r=this.jt.bh();return n&&0!==r.length&&(e+=`${r} `),i&&s&&(e+=this.jt.Dt().Mh()?t.xh:t.Sh),e.trim()}wh(t,i,n){return i?n?this.jt.Dt().Mh()?t.Sh:t.xh:t.Kt:\"\"}}function ki(t,i,n,s){const e=Number.isFinite(i),r=Number.isFinite(n);return e&&r?t(i,n):e||r?e?i:n:s}class yi{constructor(t,i){this.kh=t,this.yh=i}Ch(t){return null!==t&&(this.kh===t.kh&&this.yh===t.yh)}Th(){return new yi(this.kh,this.yh)}Ph(){return this.kh}Rh(){return this.yh}Dh(){return this.yh-this.kh}Ni(){return this.yh===this.kh||Number.isNaN(this.yh)||Number.isNaN(this.kh)}ts(t){return null===t?this:new yi(ki(Math.min,this.Ph(),t.Ph(),-1/0),ki(Math.max,this.Rh(),t.Rh(),1/0))}Oh(t){if(!P(t))return;if(0===this.yh-this.kh)return;const i=.5*(this.yh+this.kh);let n=this.yh-i,s=this.kh-i;n*=t,s*=t,this.yh=i+n,this.kh=i+s}Bh(t){P(t)&&(this.yh+=t,this.kh+=t)}Vh(){return{minValue:this.kh,maxValue:this.yh}}static Ah(t){return null===t?null:new yi(t.minValue,t.maxValue)}}class Ci{constructor(t,i){this.zh=t,this.Eh=i||null}Ih(){return this.zh}Lh(){return this.Eh}Vh(){return null===this.zh?null:{priceRange:this.zh.Vh(),margins:this.Eh||void 0}}static Ah(t){return null===t?null:new Ci(yi.Ah(t.priceRange),t.margins)}}class Ti extends ni{constructor(t,i){super(t),this.Nh=i}yr(){const t=this.Sr;t.yt=!1;const i=this.Nh.W();if(!this.Ls.yt()||!i.lineVisible)return;const n=this.Nh.Fh();null!==n&&(t.yt=!0,t.st=n,t.O=i.color,t.et=i.lineWidth,t.Nt=i.lineStyle,t.gr=this.Nh.W().id)}}class Pi extends J{constructor(t,i){super(),this.jr=t,this.Nh=i}Ei(t,i,n){t.yt=!1,i.yt=!1;const s=this.Nh.W(),e=s.axisLabelVisible,r=\"\"!==s.title,h=this.jr;if(!e||!h.yt())return;const l=this.Nh.Fh();if(null===l)return;r&&(i.Kt=s.title,i.yt=!0),i.Bt=h.$t().Vt(l/h.Dt().At()),t.Kt=this.Wh(s.price),t.yt=!0;const a=y(s.axisLabelColor||s.color);n.t=a.t;const o=s.axisLabelTextColor||a.i;t.O=o,i.O=o,n.ki=l}Wh(t){const i=this.jr.Ct();return null===i?\"\":this.jr.Dt().Fi(t,i.Ot)}}class Ri{constructor(t,i){this.jr=t,this.cn=i,this.jh=new Ti(t,this),this.ur=new Pi(t,this),this.Hh=new ti(this.ur,t,t.$t())}$h(t){T(this.cn,t),this.bt(),this.jr.$t().Uh()}W(){return this.cn}qh(){return this.jh}Yh(){return this.Hh}Zh(){return this.ur}bt(){this.jh.bt(),this.ur.bt()}Fh(){const t=this.jr,i=t.Dt();if(t.$t().St().Ni()||i.Ni())return null;const n=t.Ct();return null===n?null:i.Rt(this.cn.price,n.Ot)}}class Di extends st{constructor(t){super(),this.$i=t}$t(){return this.$i}}const Oi={Bar:(t,i,n,s)=>{var e;const r=i.upColor,h=i.downColor,l=f(t(n,s)),a=v(l.Ot[0])<=v(l.Ot[3]);return{ce:null!==(e=l.O)&&void 0!==e?e:a?r:h}},Candlestick:(t,i,n,s)=>{var e,r,h;const l=i.upColor,a=i.downColor,o=i.borderUpColor,_=i.borderDownColor,u=i.wickUpColor,c=i.wickDownColor,d=f(t(n,s)),p=v(d.Ot[0])<=v(d.Ot[3]);return{ce:null!==(e=d.O)&&void 0!==e?e:p?l:a,Ne:null!==(r=d.Bt)&&void 0!==r?r:p?o:_,Le:null!==(h=d.Xh)&&void 0!==h?h:p?u:c}},Custom:(t,i,n,s)=>{var e;return{ce:null!==(e=f(t(n,s)).O)&&void 0!==e?e:i.color}},Area:(t,i,n,s)=>{var e,r,h,l;const a=f(t(n,s));return{ce:null!==(e=a.lt)&&void 0!==e?e:i.lineColor,lt:null!==(r=a.lt)&&void 0!==r?r:i.lineColor,Ps:null!==(h=a.Ps)&&void 0!==h?h:i.topColor,Rs:null!==(l=a.Rs)&&void 0!==l?l:i.bottomColor}},Baseline:(t,i,n,s)=>{var e,r,h,l,a,o;const _=f(t(n,s));return{ce:_.Ot[3]>=i.baseValue.price?i.topLineColor:i.bottomLineColor,Re:null!==(e=_.Re)&&void 0!==e?e:i.topLineColor,De:null!==(r=_.De)&&void 0!==r?r:i.bottomLineColor,ke:null!==(h=_.ke)&&void 0!==h?h:i.topFillColor1,ye:null!==(l=_.ye)&&void 0!==l?l:i.topFillColor2,Ce:null!==(a=_.Ce)&&void 0!==a?a:i.bottomFillColor1,Te:null!==(o=_.Te)&&void 0!==o?o:i.bottomFillColor2}},Line:(t,i,n,s)=>{var e,r;const h=f(t(n,s));return{ce:null!==(e=h.O)&&void 0!==e?e:i.color,lt:null!==(r=h.O)&&void 0!==r?r:i.color}},Histogram:(t,i,n,s)=>{var e;return{ce:null!==(e=f(t(n,s)).O)&&void 0!==e?e:i.color}}};class Bi{constructor(t){this.Kh=(t,i)=>void 0!==i?i.Ot:this.jr.zn().Gh(t),this.jr=t,this.Jh=Oi[t.Qh()]}$s(t,i){return this.Jh(this.Kh,this.jr.W(),t,i)}}var Vi;!function(t){t[t.NearestLeft=-1]=\"NearestLeft\",t[t.None=0]=\"None\",t[t.NearestRight=1]=\"NearestRight\"}(Vi||(Vi={}));const Ai=30;class zi{constructor(){this.tl=[],this.il=new Map,this.nl=new Map}sl(){return this.Ks()>0?this.tl[this.tl.length-1]:null}el(){return this.Ks()>0?this.rl(0):null}An(){return this.Ks()>0?this.rl(this.tl.length-1):null}Ks(){return this.tl.length}Ni(){return 0===this.Ks()}Kr(t){return null!==this.hl(t,0)}Gh(t){return this.ll(t)}ll(t,i=0){const n=this.hl(t,i);return null===n?null:Object.assign(Object.assign({},this.al(n)),{ee:this.rl(n)})}ne(){return this.tl}ol(t,i,n){if(this.Ni())return null;let s=null;for(const e of n){s=Ei(s,this._l(t,i,e))}return s}J(t){this.nl.clear(),this.il.clear(),this.tl=t}rl(t){return this.tl[t].ee}al(t){return this.tl[t]}hl(t,i){const n=this.ul(t);if(null===n&&0!==i)switch(i){case-1:return this.cl(t);case 1:return this.dl(t);default:throw new TypeError(\"Unknown search mode\")}return n}cl(t){let i=this.fl(t);return i>0&&(i-=1),i!==this.tl.length&&this.rl(i)<t?i:null}dl(t){const i=this.vl(t);return i!==this.tl.length&&t<this.rl(i)?i:null}ul(t){const i=this.fl(t);return i===this.tl.length||t<this.tl[i].ee?null:i}fl(t){return Rt(this.tl,t,((t,i)=>t.ee<i))}vl(t){return Dt(this.tl,t,((t,i)=>t.ee>i))}pl(t,i,n){let s=null;for(let e=t;e<i;e++){const t=this.tl[e].Ot[n];Number.isNaN(t)||(null===s?s={ml:t,bl:t}:(t<s.ml&&(s.ml=t),t>s.bl&&(s.bl=t)))}return s}_l(t,i,n){if(this.Ni())return null;let s=null;const e=f(this.el()),r=f(this.An()),h=Math.max(t,e),l=Math.min(i,r),a=Math.ceil(h/Ai)*Ai,o=Math.max(a,Math.floor(l/Ai)*Ai);{const t=this.fl(h),e=this.vl(Math.min(l,a,i));s=Ei(s,this.pl(t,e,n))}let _=this.il.get(n);void 0===_&&(_=new Map,this.il.set(n,_));for(let t=Math.max(a+1,h);t<o;t+=Ai){const i=Math.floor(t/Ai);let e=_.get(i);if(void 0===e){const t=this.fl(i*Ai),s=this.vl((i+1)*Ai-1);e=this.pl(t,s,n),_.set(i,e)}s=Ei(s,e)}{const t=this.fl(o),i=this.vl(l);s=Ei(s,this.pl(t,i,n))}return s}}function Ei(t,i){if(null===t)return i;if(null===i)return t;return{ml:Math.min(t.ml,i.ml),bl:Math.max(t.bl,i.bl)}}class Ii{constructor(t){this.wl=t}X(t,i,n){this.wl.draw(t)}gl(t,i,n){var s,e;null===(e=(s=this.wl).drawBackground)||void 0===e||e.call(s,t)}}class Li{constructor(t){this.tr=null,this.wn=t}gt(){var t;const i=this.wn.renderer();if(null===i)return null;if((null===(t=this.tr)||void 0===t?void 0:t.Ml)===i)return this.tr.xl;const n=new Ii(i);return this.tr={Ml:i,xl:n},n}Sl(){var t,i,n;return null!==(n=null===(i=(t=this.wn).zOrder)||void 0===i?void 0:i.call(t))&&void 0!==n?n:\"normal\"}}function Ni(t){var i,n,s,e,r;return{Kt:t.text(),ki:t.coordinate(),Si:null===(i=t.fixedCoordinate)||void 0===i?void 0:i.call(t),O:t.textColor(),t:t.backColor(),yt:null===(s=null===(n=t.visible)||void 0===n?void 0:n.call(t))||void 0===s||s,hi:null===(r=null===(e=t.tickVisible)||void 0===e?void 0:e.call(t))||void 0===r||r}}class Fi{constructor(t,i){this.Wt=new it,this.kl=t,this.yl=i}gt(){return this.Wt.J(Object.assign({Hi:this.yl.Hi()},Ni(this.kl))),this.Wt}}class Wi extends J{constructor(t,i){super(),this.kl=t,this.Ii=i}Ei(t,i,n){const s=Ni(this.kl);n.t=s.t,t.O=s.O;const e=2/12*this.Ii.P();n.wi=e,n.gi=e,n.ki=s.ki,n.Si=s.Si,t.Kt=s.Kt,t.yt=s.yt,t.hi=s.hi}}class ji{constructor(t,i){this.Cl=null,this.Tl=null,this.Pl=null,this.Rl=null,this.Dl=null,this.Ol=t,this.jr=i}Bl(){return this.Ol}On(){var t,i;null===(i=(t=this.Ol).updateAllViews)||void 0===i||i.call(t)}Pn(){var t,i,n,s;const e=null!==(n=null===(i=(t=this.Ol).paneViews)||void 0===i?void 0:i.call(t))&&void 0!==n?n:[];if((null===(s=this.Cl)||void 0===s?void 0:s.Ml)===e)return this.Cl.xl;const r=e.map((t=>new Li(t)));return this.Cl={Ml:e,xl:r},r}Qi(){var t,i,n,s;const e=null!==(n=null===(i=(t=this.Ol).timeAxisViews)||void 0===i?void 0:i.call(t))&&void 0!==n?n:[];if((null===(s=this.Tl)||void 0===s?void 0:s.Ml)===e)return this.Tl.xl;const r=this.jr.$t().St(),h=e.map((t=>new Fi(t,r)));return this.Tl={Ml:e,xl:h},h}Rn(){var t,i,n,s;const e=null!==(n=null===(i=(t=this.Ol).priceAxisViews)||void 0===i?void 0:i.call(t))&&void 0!==n?n:[];if((null===(s=this.Pl)||void 0===s?void 0:s.Ml)===e)return this.Pl.xl;const r=this.jr.Dt(),h=e.map((t=>new Wi(t,r)));return this.Pl={Ml:e,xl:h},h}Vl(){var t,i,n,s;const e=null!==(n=null===(i=(t=this.Ol).priceAxisPaneViews)||void 0===i?void 0:i.call(t))&&void 0!==n?n:[];if((null===(s=this.Rl)||void 0===s?void 0:s.Ml)===e)return this.Rl.xl;const r=e.map((t=>new Li(t)));return this.Rl={Ml:e,xl:r},r}Al(){var t,i,n,s;const e=null!==(n=null===(i=(t=this.Ol).timeAxisPaneViews)||void 0===i?void 0:i.call(t))&&void 0!==n?n:[];if((null===(s=this.Dl)||void 0===s?void 0:s.Ml)===e)return this.Dl.xl;const r=e.map((t=>new Li(t)));return this.Dl={Ml:e,xl:r},r}zl(t,i){var n,s,e;return null!==(e=null===(s=(n=this.Ol).autoscaleInfo)||void 0===s?void 0:s.call(n,t,i))&&void 0!==e?e:null}wr(t,i){var n,s,e;return null!==(e=null===(s=(n=this.Ol).hitTest)||void 0===s?void 0:s.call(n,t,i))&&void 0!==e?e:null}}function Hi(t,i,n,s){t.forEach((t=>{i(t).forEach((t=>{t.Sl()===n&&s.push(t)}))}))}function $i(t){return t.Pn()}function Ui(t){return t.Vl()}function qi(t){return t.Al()}class Yi extends Di{constructor(t,i,n,s,e){super(t),this.Et=new zi,this.jh=new xi(this),this.El=[],this.Il=new si(this),this.Ll=null,this.Nl=null,this.Fl=[],this.Wl=[],this.jl=null,this.Hl=[],this.cn=i,this.$l=n;const r=new Si(this);this.rn=[r],this.Hh=new ti(r,this,t),\"Area\"!==n&&\"Line\"!==n&&\"Baseline\"!==n||(this.Ll=new ai(this)),this.Ul(),this.ql(e)}S(){null!==this.jl&&clearTimeout(this.jl)}mh(t){return this.cn.priceLineColor||t}Zr(t){const i={Xr:!0},n=this.Dt();if(this.$t().St().Ni()||n.Ni()||this.Et.Ni())return i;const s=this.$t().St().Xs(),e=this.Ct();if(null===s||null===e)return i;let r,h;if(t){const t=this.Et.sl();if(null===t)return i;r=t,h=t.ee}else{const t=this.Et.ll(s.ui(),-1);if(null===t)return i;if(r=this.Et.Gh(t.ee),null===r)return i;h=t.ee}const l=r.Ot[3],a=this.Us().$s(h,{Ot:r}),o=n.Rt(l,e.Ot);return{Xr:!1,_t:l,Kt:n.Fi(l,e.Ot),xh:n.Yl(l),Sh:n.Zl(l,e.Ot),O:a.ce,ki:o,ee:h}}Us(){return null!==this.Nl||(this.Nl=new Bi(this)),this.Nl}W(){return this.cn}$h(t){const i=t.priceScaleId;void 0!==i&&i!==this.cn.priceScaleId&&this.$t().Xl(this,i),T(this.cn,t),void 0!==t.priceFormat&&(this.Ul(),this.$t().Kl()),this.$t().Gl(this),this.$t().Jl(),this.wn.bt(\"options\")}J(t,i){this.Et.J(t),this.Ql(),this.wn.bt(\"data\"),this.dn.bt(\"data\"),null!==this.Ll&&(i&&i.ta?this.Ll.$r():0===t.length&&this.Ll.Hr());const n=this.$t().dr(this);this.$t().ia(n),this.$t().Gl(this),this.$t().Jl(),this.$t().Uh()}na(t){this.Fl=t,this.Ql();const i=this.$t().dr(this);this.dn.bt(\"data\"),this.$t().ia(i),this.$t().Gl(this),this.$t().Jl(),this.$t().Uh()}sa(){return this.Fl}dh(){return this.Wl}ea(t){const i=new Ri(this,t);return this.El.push(i),this.$t().Gl(this),i}ra(t){const i=this.El.indexOf(t);-1!==i&&this.El.splice(i,1),this.$t().Gl(this)}Qh(){return this.$l}Ct(){const t=this.ha();return null===t?null:{Ot:t.Ot[3],la:t.ot}}ha(){const t=this.$t().St().Xs();if(null===t)return null;const i=t.Bs();return this.Et.ll(i,1)}zn(){return this.Et}ph(t){const i=this.Et.Gh(t);return null===i?null:\"Bar\"===this.$l||\"Candlestick\"===this.$l||\"Custom\"===this.$l?{ge:i.Ot[0],Me:i.Ot[1],xe:i.Ot[2],Se:i.Ot[3]}:i.Ot[3]}aa(t){const i=[];Hi(this.Hl,$i,\"top\",i);const n=this.Ll;return null!==n&&n.yt()?(null===this.jl&&n.qr()&&(this.jl=setTimeout((()=>{this.jl=null,this.$t().oa()}),0)),n.Ur(),i.unshift(n),i):i}Pn(){const t=[];this._a()||t.push(this.Il),t.push(this.wn,this.jh,this.dn);const i=this.El.map((t=>t.qh()));return t.push(...i),Hi(this.Hl,$i,\"normal\",t),t}ua(){return this.ca($i,\"bottom\")}da(t){return this.ca(Ui,t)}fa(t){return this.ca(qi,t)}va(t,i){return this.Hl.map((n=>n.wr(t,i))).filter((t=>null!==t))}Ji(t){return[this.Hh,...this.El.map((t=>t.Yh()))]}Rn(t,i){if(i!==this.Yi&&!this._a())return[];const n=[...this.rn];for(const t of this.El)n.push(t.Zh());return this.Hl.forEach((t=>{n.push(...t.Rn())})),n}Qi(){const t=[];return this.Hl.forEach((i=>{t.push(...i.Qi())})),t}zl(t,i){if(void 0!==this.cn.autoscaleInfoProvider){const n=this.cn.autoscaleInfoProvider((()=>{const n=this.pa(t,i);return null===n?null:n.Vh()}));return Ci.Ah(n)}return this.pa(t,i)}ma(){return this.cn.priceFormat.minMove}ba(){return this.wa}On(){var t;this.wn.bt(),this.dn.bt();for(const t of this.rn)t.bt();for(const t of this.El)t.bt();this.jh.bt(),this.Il.bt(),null===(t=this.Ll)||void 0===t||t.bt(),this.Hl.forEach((t=>t.On()))}Dt(){return f(super.Dt())}kt(t){if(!((\"Line\"===this.$l||\"Area\"===this.$l||\"Baseline\"===this.$l)&&this.cn.crosshairMarkerVisible))return null;const i=this.Et.Gh(t);if(null===i)return null;return{_t:i.Ot[3],ht:this.ga(),Bt:this.Ma(),Pt:this.xa(),Tt:this.Sa(t)}}bh(){return this.cn.title}yt(){return this.cn.visible}ka(t){this.Hl.push(new ji(t,this))}ya(t){this.Hl=this.Hl.filter((i=>i.Bl()!==t))}Ca(){if(this.wn instanceof qt!=!1)return t=>this.wn.We(t)}Ta(){if(this.wn instanceof qt!=!1)return t=>this.wn.je(t)}_a(){return!ht(this.Dt().Pa())}pa(t,i){if(!R(t)||!R(i)||this.Et.Ni())return null;const n=\"Line\"===this.$l||\"Area\"===this.$l||\"Baseline\"===this.$l||\"Histogram\"===this.$l?[3]:[2,1],s=this.Et.ol(t,i,n);let e=null!==s?new yi(s.ml,s.bl):null;if(\"Histogram\"===this.Qh()){const t=this.cn.base,i=new yi(t,t);e=null!==e?e.ts(i):i}let r=this.dn.uh();return this.Hl.forEach((n=>{const s=n.zl(t,i);if(null==s?void 0:s.priceRange){const t=new yi(s.priceRange.minValue,s.priceRange.maxValue);e=null!==e?e.ts(t):t}var h,l,a,o;(null==s?void 0:s.margins)&&(h=r,l=s.margins,r={above:Math.max(null!==(a=null==h?void 0:h.above)&&void 0!==a?a:0,l.above),below:Math.max(null!==(o=null==h?void 0:h.below)&&void 0!==o?o:0,l.below)})})),new Ci(e,r)}ga(){switch(this.$l){case\"Line\":case\"Area\":case\"Baseline\":return this.cn.crosshairMarkerRadius}return 0}Ma(){switch(this.$l){case\"Line\":case\"Area\":case\"Baseline\":{const t=this.cn.crosshairMarkerBorderColor;if(0!==t.length)return t}}return null}xa(){switch(this.$l){case\"Line\":case\"Area\":case\"Baseline\":return this.cn.crosshairMarkerBorderWidth}return 0}Sa(t){switch(this.$l){case\"Line\":case\"Area\":case\"Baseline\":{const t=this.cn.crosshairMarkerBackgroundColor;if(0!==t.length)return t}}return this.Us().$s(t).ce}Ul(){switch(this.cn.priceFormat.type){case\"custom\":this.wa={format:this.cn.priceFormat.formatter};break;case\"volume\":this.wa=new ct(this.cn.priceFormat.precision);break;case\"percent\":this.wa=new ut(this.cn.priceFormat.precision);break;default:{const t=Math.pow(10,this.cn.priceFormat.precision);this.wa=new _t(t,this.cn.priceFormat.minMove*t)}}null!==this.Yi&&this.Yi.Ra()}Ql(){const t=this.$t().St();if(!t.Da()||this.Et.Ni())return void(this.Wl=[]);const i=f(this.Et.el());this.Wl=this.Fl.map(((n,s)=>{const e=f(t.Oa(n.time,!0)),r=e<i?1:-1;return{time:f(this.Et.ll(e,r)).ee,position:n.position,shape:n.shape,color:n.color,id:n.id,th:s,text:n.text,size:n.size,originalTime:n.originalTime}}))}ql(t){switch(this.dn=new Mi(this,this.$t()),this.$l){case\"Bar\":this.wn=new Nt(this,this.$t());break;case\"Candlestick\":this.wn=new $t(this,this.$t());break;case\"Line\":this.wn=new Kt(this,this.$t());break;case\"Custom\":this.wn=new qt(this,this.$t(),d(t));break;case\"Area\":this.wn=new Et(this,this.$t());break;case\"Baseline\":this.wn=new jt(this,this.$t());break;case\"Histogram\":this.wn=new Xt(this,this.$t());break;default:throw Error(\"Unknown chart style assigned: \"+this.$l)}}ca(t,i){const n=[];return Hi(this.Hl,t,i,n),n}}class Zi{constructor(t){this.cn=t}Ba(t,i,n){let s=t;if(0===this.cn.mode)return s;const e=n.vn(),r=e.Ct();if(null===r)return s;const h=e.Rt(t,r),l=n.Va().filter((t=>t instanceof Yi)).reduce(((t,s)=>{if(n.vr(s)||!s.yt())return t;const e=s.Dt(),r=s.zn();if(e.Ni()||!r.Kr(i))return t;const h=r.Gh(i);if(null===h)return t;const l=v(s.Ct());return t.concat([e.Rt(h.Ot[3],l.Ot)])}),[]);if(0===l.length)return s;l.sort(((t,i)=>Math.abs(t-h)-Math.abs(i-h)));const a=l[0];return s=e.pn(a,r),s}}class Xi extends N{constructor(){super(...arguments),this.Et=null}J(t){this.Et=t}K({context:t,bitmapSize:i,horizontalPixelRatio:n,verticalPixelRatio:s}){if(null===this.Et)return;const e=Math.max(1,Math.floor(n));t.lineWidth=e,function(t,i){t.save(),t.lineWidth%2&&t.translate(.5,.5),i(),t.restore()}(t,(()=>{const r=f(this.Et);if(r.Aa){t.strokeStyle=r.za,_(t,r.Ea),t.beginPath();for(const s of r.Ia){const r=Math.round(s.La*n);t.moveTo(r,-e),t.lineTo(r,i.height+e)}t.stroke()}if(r.Na){t.strokeStyle=r.Fa,_(t,r.Wa),t.beginPath();for(const n of r.ja){const r=Math.round(n.La*s);t.moveTo(-e,r),t.lineTo(i.width+e,r)}t.stroke()}}))}}class Ki{constructor(t){this.Wt=new Xi,this.ft=!0,this.tn=t}bt(){this.ft=!0}gt(){if(this.ft){const t=this.tn.$t().W().grid,i={Na:t.horzLines.visible,Aa:t.vertLines.visible,Fa:t.horzLines.color,za:t.vertLines.color,Wa:t.horzLines.style,Ea:t.vertLines.style,ja:this.tn.vn().Ha(),Ia:(this.tn.$t().St().Ha()||[]).map((t=>({La:t.coord})))};this.Wt.J(i),this.ft=!1}return this.Wt}}class Gi{constructor(t){this.wn=new Ki(t)}qh(){return this.wn}}const Ji={$a:4,Ua:1e-4};function Qi(t,i){const n=100*(t-i)/i;return i<0?-n:n}function tn(t,i){const n=Qi(t.Ph(),i),s=Qi(t.Rh(),i);return new yi(n,s)}function nn(t,i){const n=100*(t-i)/i+100;return i<0?-n:n}function sn(t,i){const n=nn(t.Ph(),i),s=nn(t.Rh(),i);return new yi(n,s)}function en(t,i){const n=Math.abs(t);if(n<1e-15)return 0;const s=Math.log10(n+i.Ua)+i.$a;return t<0?-s:s}function rn(t,i){const n=Math.abs(t);if(n<1e-15)return 0;const s=Math.pow(10,n-i.$a)-i.Ua;return t<0?-s:s}function hn(t,i){if(null===t)return null;const n=en(t.Ph(),i),s=en(t.Rh(),i);return new yi(n,s)}function ln(t,i){if(null===t)return null;const n=rn(t.Ph(),i),s=rn(t.Rh(),i);return new yi(n,s)}function an(t){if(null===t)return Ji;const i=Math.abs(t.Rh()-t.Ph());if(i>=1||i<1e-15)return Ji;const n=Math.ceil(Math.abs(Math.log10(i))),s=Ji.$a+n;return{$a:s,Ua:1/Math.pow(10,s)}}class on{constructor(t,i){if(this.qa=t,this.Ya=i,function(t){if(t<0)return!1;for(let i=t;i>1;i/=10)if(i%10!=0)return!1;return!0}(this.qa))this.Za=[2,2.5,2];else{this.Za=[];for(let t=this.qa;1!==t;){if(t%2==0)this.Za.push(2),t/=2;else{if(t%5!=0)throw new Error(\"unexpected base\");this.Za.push(2,2.5),t/=5}if(this.Za.length>100)throw new Error(\"something wrong with base\")}}}Xa(t,i,n){const s=0===this.qa?0:1/this.qa;let e=Math.pow(10,Math.max(0,Math.ceil(Math.log10(t-i)))),r=0,h=this.Ya[0];for(;;){const t=Mt(e,s,1e-14)&&e>s+1e-14,i=Mt(e,n*h,1e-14),l=Mt(e,1,1e-14);if(!(t&&i&&l))break;e/=h,h=this.Ya[++r%this.Ya.length]}if(e<=s+1e-14&&(e=s),e=Math.max(1,e),this.Za.length>0&&(l=e,a=1,o=1e-14,Math.abs(l-a)<o))for(r=0,h=this.Za[0];Mt(e,n*h,1e-14)&&e>s+1e-14;)e/=h,h=this.Za[++r%this.Za.length];var l,a,o;return e}}class _n{constructor(t,i,n,s){this.Ka=[],this.Ii=t,this.qa=i,this.Ga=n,this.Ja=s}Xa(t,i){if(t<i)throw new Error(\"high < low\");const n=this.Ii.At(),s=(t-i)*this.Qa()/n,e=new on(this.qa,[2,2.5,2]),r=new on(this.qa,[2,2,2.5]),h=new on(this.qa,[2.5,2,2]),l=[];return l.push(e.Xa(t,i,s),r.Xa(t,i,s),h.Xa(t,i,s)),function(t){if(t.length<1)throw Error(\"array is empty\");let i=t[0];for(let n=1;n<t.length;++n)t[n]<i&&(i=t[n]);return i}(l)}io(){const t=this.Ii,i=t.Ct();if(null===i)return void(this.Ka=[]);const n=t.At(),s=this.Ga(n-1,i),e=this.Ga(0,i),r=this.Ii.W().entireTextOnly?this.no()/2:0,h=r,l=n-1-r,a=Math.max(s,e),o=Math.min(s,e);if(a===o)return void(this.Ka=[]);let _=this.Xa(a,o),u=a%_;u+=u<0?_:0;const c=a>=o?1:-1;let d=null,f=0;for(let n=a-u;n>o;n-=_){const s=this.Ja(n,i,!0);null!==d&&Math.abs(s-d)<this.Qa()||(s<h||s>l||(f<this.Ka.length?(this.Ka[f].La=s,this.Ka[f].so=t.eo(n)):this.Ka.push({La:s,so:t.eo(n)}),f++,d=s,t.ro()&&(_=this.Xa(n*c,o))))}this.Ka.length=f}Ha(){return this.Ka}no(){return this.Ii.P()}Qa(){return Math.ceil(2.5*this.no())}}function un(t){return t.slice().sort(((t,i)=>f(t.Xi())-f(i.Xi())))}var cn;!function(t){t[t.Normal=0]=\"Normal\",t[t.Logarithmic=1]=\"Logarithmic\",t[t.Percentage=2]=\"Percentage\",t[t.IndexedTo100=3]=\"IndexedTo100\"}(cn||(cn={}));const dn=new ut,fn=new _t(100,1);class vn{constructor(t,i,n,s){this.ho=0,this.lo=null,this.zh=null,this.ao=null,this.oo={_o:!1,uo:null},this.co=0,this.do=0,this.fo=new C,this.vo=new C,this.po=[],this.mo=null,this.bo=null,this.wo=null,this.Mo=null,this.wa=fn,this.xo=an(null),this.So=t,this.cn=i,this.ko=n,this.yo=s,this.Co=new _n(this,100,this.To.bind(this),this.Po.bind(this))}Pa(){return this.So}W(){return this.cn}$h(t){if(T(this.cn,t),this.Ra(),void 0!==t.mode&&this.Ro({Cr:t.mode}),void 0!==t.scaleMargins){const i=d(t.scaleMargins.top),n=d(t.scaleMargins.bottom);if(i<0||i>1)throw new Error(`Invalid top margin - expect value between 0 and 1, given=${i}`);if(n<0||n>1)throw new Error(`Invalid bottom margin - expect value between 0 and 1, given=${n}`);if(i+n>1)throw new Error(`Invalid margins - sum of margins must be less than 1, given=${i+n}`);this.Do(),this.bo=null}}Oo(){return this.cn.autoScale}ro(){return 1===this.cn.mode}Mh(){return 2===this.cn.mode}Bo(){return 3===this.cn.mode}Cr(){return{Wn:this.cn.autoScale,Vo:this.cn.invertScale,Cr:this.cn.mode}}Ro(t){const i=this.Cr();let n=null;void 0!==t.Wn&&(this.cn.autoScale=t.Wn),void 0!==t.Cr&&(this.cn.mode=t.Cr,2!==t.Cr&&3!==t.Cr||(this.cn.autoScale=!0),this.oo._o=!1),1===i.Cr&&t.Cr!==i.Cr&&(!function(t,i){if(null===t)return!1;const n=rn(t.Ph(),i),s=rn(t.Rh(),i);return isFinite(n)&&isFinite(s)}(this.zh,this.xo)?this.cn.autoScale=!0:(n=ln(this.zh,this.xo),null!==n&&this.Ao(n))),1===t.Cr&&t.Cr!==i.Cr&&(n=hn(this.zh,this.xo),null!==n&&this.Ao(n));const s=i.Cr!==this.cn.mode;s&&(2===i.Cr||this.Mh())&&this.Ra(),s&&(3===i.Cr||this.Bo())&&this.Ra(),void 0!==t.Vo&&i.Vo!==t.Vo&&(this.cn.invertScale=t.Vo,this.zo()),this.vo.m(i,this.Cr())}Eo(){return this.vo}P(){return this.ko.fontSize}At(){return this.ho}Io(t){this.ho!==t&&(this.ho=t,this.Do(),this.bo=null)}Lo(){if(this.lo)return this.lo;const t=this.At()-this.No()-this.Fo();return this.lo=t,t}Ih(){return this.Wo(),this.zh}Ao(t,i){const n=this.zh;(i||null===n&&null!==t||null!==n&&!n.Ch(t))&&(this.bo=null,this.zh=t)}Ni(){return this.Wo(),0===this.ho||!this.zh||this.zh.Ni()}jo(t){return this.Vo()?t:this.At()-1-t}Rt(t,i){return this.Mh()?t=Qi(t,i):this.Bo()&&(t=nn(t,i)),this.Po(t,i)}te(t,i,n){this.Wo();const s=this.Fo(),e=f(this.Ih()),r=e.Ph(),h=e.Rh(),l=this.Lo()-1,a=this.Vo(),o=l/(h-r),_=void 0===n?0:n.from,u=void 0===n?t.length:n.to,c=this.Ho();for(let n=_;n<u;n++){const e=t[n],h=e._t;if(isNaN(h))continue;let l=h;null!==c&&(l=c(e._t,i));const _=s+o*(l-r),u=a?_:this.ho-1-_;e.st=u}}be(t,i,n){this.Wo();const s=this.Fo(),e=f(this.Ih()),r=e.Ph(),h=e.Rh(),l=this.Lo()-1,a=this.Vo(),o=l/(h-r),_=void 0===n?0:n.from,u=void 0===n?t.length:n.to,c=this.Ho();for(let n=_;n<u;n++){const e=t[n];let h=e.ge,l=e.Me,_=e.xe,u=e.Se;null!==c&&(h=c(e.ge,i),l=c(e.Me,i),_=c(e.xe,i),u=c(e.Se,i));let d=s+o*(h-r),f=a?d:this.ho-1-d;e.pe=f,d=s+o*(l-r),f=a?d:this.ho-1-d,e.de=f,d=s+o*(_-r),f=a?d:this.ho-1-d,e.fe=f,d=s+o*(u-r),f=a?d:this.ho-1-d,e.me=f}}pn(t,i){const n=this.To(t,i);return this.$o(n,i)}$o(t,i){let n=t;return this.Mh()?n=function(t,i){return i<0&&(t=-t),t/100*i+i}(n,i):this.Bo()&&(n=function(t,i){return t-=100,i<0&&(t=-t),t/100*i+i}(n,i)),n}Va(){return this.po}Uo(){if(this.mo)return this.mo;let t=[];for(let i=0;i<this.po.length;i++){const n=this.po[i];null===n.Xi()&&n.Ki(i+1),t.push(n)}return t=un(t),this.mo=t,this.mo}qo(t){-1===this.po.indexOf(t)&&(this.po.push(t),this.Ra(),this.Yo())}Zo(t){const i=this.po.indexOf(t);if(-1===i)throw new Error(\"source is not attached to scale\");this.po.splice(i,1),0===this.po.length&&(this.Ro({Wn:!0}),this.Ao(null)),this.Ra(),this.Yo()}Ct(){let t=null;for(const i of this.po){const n=i.Ct();null!==n&&((null===t||n.la<t.la)&&(t=n))}return null===t?null:t.Ot}Vo(){return this.cn.invertScale}Ha(){const t=null===this.Ct();if(null!==this.bo&&(t||this.bo.Xo===t))return this.bo.Ha;this.Co.io();const i=this.Co.Ha();return this.bo={Ha:i,Xo:t},this.fo.m(),i}Ko(){return this.fo}Go(t){this.Mh()||this.Bo()||null===this.wo&&null===this.ao&&(this.Ni()||(this.wo=this.ho-t,this.ao=f(this.Ih()).Th()))}Jo(t){if(this.Mh()||this.Bo())return;if(null===this.wo)return;this.Ro({Wn:!1}),(t=this.ho-t)<0&&(t=0);let i=(this.wo+.2*(this.ho-1))/(t+.2*(this.ho-1));const n=f(this.ao).Th();i=Math.max(i,.1),n.Oh(i),this.Ao(n)}Qo(){this.Mh()||this.Bo()||(this.wo=null,this.ao=null)}t_(t){this.Oo()||null===this.Mo&&null===this.ao&&(this.Ni()||(this.Mo=t,this.ao=f(this.Ih()).Th()))}i_(t){if(this.Oo())return;if(null===this.Mo)return;const i=f(this.Ih()).Dh()/(this.Lo()-1);let n=t-this.Mo;this.Vo()&&(n*=-1);const s=n*i,e=f(this.ao).Th();e.Bh(s),this.Ao(e,!0),this.bo=null}n_(){this.Oo()||null!==this.Mo&&(this.Mo=null,this.ao=null)}ba(){return this.wa||this.Ra(),this.wa}Fi(t,i){switch(this.cn.mode){case 2:return this.s_(Qi(t,i));case 3:return this.ba().format(nn(t,i));default:return this.Wh(t)}}eo(t){switch(this.cn.mode){case 2:return this.s_(t);case 3:return this.ba().format(t);default:return this.Wh(t)}}Yl(t){return this.Wh(t,f(this.e_()).ba())}Zl(t,i){return t=Qi(t,i),this.s_(t,dn)}r_(){return this.po}h_(t){this.oo={uo:t,_o:!1}}On(){this.po.forEach((t=>t.On()))}Ra(){this.bo=null;const t=this.e_();let i=100;null!==t&&(i=Math.round(1/t.ma())),this.wa=fn,this.Mh()?(this.wa=dn,i=100):this.Bo()?(this.wa=new _t(100,1),i=100):null!==t&&(this.wa=t.ba()),this.Co=new _n(this,i,this.To.bind(this),this.Po.bind(this)),this.Co.io()}Yo(){this.mo=null}e_(){return this.po[0]||null}No(){return this.Vo()?this.cn.scaleMargins.bottom*this.At()+this.do:this.cn.scaleMargins.top*this.At()+this.co}Fo(){return this.Vo()?this.cn.scaleMargins.top*this.At()+this.co:this.cn.scaleMargins.bottom*this.At()+this.do}Wo(){this.oo._o||(this.oo._o=!0,this.l_())}Do(){this.lo=null}Po(t,i){if(this.Wo(),this.Ni())return 0;t=this.ro()&&t?en(t,this.xo):t;const n=f(this.Ih()),s=this.Fo()+(this.Lo()-1)*(t-n.Ph())/n.Dh();return this.jo(s)}To(t,i){if(this.Wo(),this.Ni())return 0;const n=this.jo(t),s=f(this.Ih()),e=s.Ph()+s.Dh()*((n-this.Fo())/(this.Lo()-1));return this.ro()?rn(e,this.xo):e}zo(){this.bo=null,this.Co.io()}l_(){const t=this.oo.uo;if(null===t)return;let i=null;const n=this.r_();let s=0,e=0;for(const r of n){if(!r.yt())continue;const n=r.Ct();if(null===n)continue;const h=r.zl(t.Bs(),t.ui());let l=h&&h.Ih();if(null!==l){switch(this.cn.mode){case 1:l=hn(l,this.xo);break;case 2:l=tn(l,n.Ot);break;case 3:l=sn(l,n.Ot)}if(i=null===i?l:i.ts(f(l)),null!==h){const t=h.Lh();null!==t&&(s=Math.max(s,t.above),e=Math.max(e,t.below))}}}if(s===this.co&&e===this.do||(this.co=s,this.do=e,this.bo=null,this.Do()),null!==i){if(i.Ph()===i.Rh()){const t=this.e_(),n=5*(null===t||this.Mh()||this.Bo()?1:t.ma());this.ro()&&(i=ln(i,this.xo)),i=new yi(i.Ph()-n,i.Rh()+n),this.ro()&&(i=hn(i,this.xo))}if(this.ro()){const t=ln(i,this.xo),n=an(t);if(r=n,h=this.xo,r.$a!==h.$a||r.Ua!==h.Ua){const s=null!==this.ao?ln(this.ao,this.xo):null;this.xo=n,i=hn(t,n),null!==s&&(this.ao=hn(s,n))}}this.Ao(i)}else null===this.zh&&(this.Ao(new yi(-.5,.5)),this.xo=an(null));var r,h;this.oo._o=!0}Ho(){return this.Mh()?Qi:this.Bo()?nn:this.ro()?t=>en(t,this.xo):null}a_(t,i,n){return void 0===i?(void 0===n&&(n=this.ba()),n.format(t)):i(t)}Wh(t,i){return this.a_(t,this.yo.priceFormatter,i)}s_(t,i){return this.a_(t,this.yo.percentageFormatter,i)}}class pn{constructor(t,i){this.po=[],this.o_=new Map,this.ho=0,this.__=0,this.u_=1e3,this.mo=null,this.c_=new C,this.yl=t,this.$i=i,this.d_=new Gi(this);const n=i.W();this.f_=this.v_(\"left\",n.leftPriceScale),this.p_=this.v_(\"right\",n.rightPriceScale),this.f_.Eo().l(this.m_.bind(this,this.f_),this),this.p_.Eo().l(this.m_.bind(this,this.p_),this),this.b_(n)}b_(t){if(t.leftPriceScale&&this.f_.$h(t.leftPriceScale),t.rightPriceScale&&this.p_.$h(t.rightPriceScale),t.localization&&(this.f_.Ra(),this.p_.Ra()),t.overlayPriceScales){const i=Array.from(this.o_.values());for(const n of i){const i=f(n[0].Dt());i.$h(t.overlayPriceScales),t.localization&&i.Ra()}}}w_(t){switch(t){case\"left\":return this.f_;case\"right\":return this.p_}return this.o_.has(t)?d(this.o_.get(t))[0].Dt():null}S(){this.$t().g_().p(this),this.f_.Eo().p(this),this.p_.Eo().p(this),this.po.forEach((t=>{t.S&&t.S()})),this.c_.m()}M_(){return this.u_}x_(t){this.u_=t}$t(){return this.$i}Hi(){return this.__}At(){return this.ho}S_(t){this.__=t,this.k_()}Io(t){this.ho=t,this.f_.Io(t),this.p_.Io(t),this.po.forEach((i=>{if(this.vr(i)){const n=i.Dt();null!==n&&n.Io(t)}})),this.k_()}Va(){return this.po}vr(t){const i=t.Dt();return null===i||this.f_!==i&&this.p_!==i}qo(t,i,n){const s=void 0!==n?n:this.C_().y_+1;this.T_(t,i,s)}Zo(t){const i=this.po.indexOf(t);c(-1!==i,\"removeDataSource: invalid data source\"),this.po.splice(i,1);const n=f(t.Dt()).Pa();if(this.o_.has(n)){const i=d(this.o_.get(n)),s=i.indexOf(t);-1!==s&&(i.splice(s,1),0===i.length&&this.o_.delete(n))}const s=t.Dt();s&&s.Va().indexOf(t)>=0&&s.Zo(t),null!==s&&(s.Yo(),this.P_(s)),this.mo=null}mr(t){return t===this.f_?\"left\":t===this.p_?\"right\":\"overlay\"}R_(){return this.f_}D_(){return this.p_}O_(t,i){t.Go(i)}B_(t,i){t.Jo(i),this.k_()}V_(t){t.Qo()}A_(t,i){t.t_(i)}z_(t,i){t.i_(i),this.k_()}E_(t){t.n_()}k_(){this.po.forEach((t=>{t.On()}))}vn(){let t=null;return this.$i.W().rightPriceScale.visible&&0!==this.p_.Va().length?t=this.p_:this.$i.W().leftPriceScale.visible&&0!==this.f_.Va().length?t=this.f_:0!==this.po.length&&(t=this.po[0].Dt()),null===t&&(t=this.p_),t}pr(){let t=null;return this.$i.W().rightPriceScale.visible?t=this.p_:this.$i.W().leftPriceScale.visible&&(t=this.f_),t}P_(t){null!==t&&t.Oo()&&this.I_(t)}L_(t){const i=this.yl.Xs();t.Ro({Wn:!0}),null!==i&&t.h_(i),this.k_()}N_(){this.I_(this.f_),this.I_(this.p_)}F_(){this.P_(this.f_),this.P_(this.p_),this.po.forEach((t=>{this.vr(t)&&this.P_(t.Dt())})),this.k_(),this.$i.Uh()}Uo(){return null===this.mo&&(this.mo=un(this.po)),this.mo}W_(){return this.c_}j_(){return this.d_}I_(t){const i=t.r_();if(i&&i.length>0&&!this.yl.Ni()){const i=this.yl.Xs();null!==i&&t.h_(i)}t.On()}C_(){const t=this.Uo();if(0===t.length)return{H_:0,y_:0};let i=0,n=0;for(let s=0;s<t.length;s++){const e=t[s].Xi();null!==e&&(e<i&&(i=e),e>n&&(n=e))}return{H_:i,y_:n}}T_(t,i,n){let s=this.w_(i);if(null===s&&(s=this.v_(i,this.$i.W().overlayPriceScales)),this.po.push(t),!ht(i)){const n=this.o_.get(i)||[];n.push(t),this.o_.set(i,n)}s.qo(t),t.Gi(s),t.Ki(n),this.P_(s),this.mo=null}m_(t,i,n){i.Cr!==n.Cr&&this.I_(t)}v_(t,i){const n=Object.assign({visible:!0,autoScale:!0},B(i)),s=new vn(t,n,this.$i.W().layout,this.$i.W().localization);return s.Io(this.At()),s}}class mn{constructor(t,i,n=50){this.Ke=0,this.Ge=1,this.Je=1,this.tr=new Map,this.Qe=new Map,this.U_=t,this.q_=i,this.ir=n}Y_(t){const i=t.time,n=this.q_.cacheKey(i),s=this.tr.get(n);if(void 0!==s)return s.Z_;if(this.Ke===this.ir){const t=this.Qe.get(this.Je);this.Qe.delete(this.Je),this.tr.delete(d(t)),this.Je++,this.Ke--}const e=this.U_(t);return this.tr.set(n,{Z_:e,rr:this.Ge}),this.Qe.set(this.Ge,n),this.Ke++,this.Ge++,e}}class bn{constructor(t,i){c(t<=i,\"right should be >= left\"),this.X_=t,this.K_=i}Bs(){return this.X_}ui(){return this.K_}G_(){return this.K_-this.X_+1}Kr(t){return this.X_<=t&&t<=this.K_}Ch(t){return this.X_===t.Bs()&&this.K_===t.ui()}}function wn(t,i){return null===t||null===i?t===i:t.Ch(i)}class gn{constructor(){this.J_=new Map,this.tr=null,this.Q_=!1}tu(t){this.Q_=t,this.tr=null}iu(t,i){this.nu(i),this.tr=null;for(let n=i;n<t.length;++n){const i=t[n];let s=this.J_.get(i.timeWeight);void 0===s&&(s=[],this.J_.set(i.timeWeight,s)),s.push({index:n,time:i.time,weight:i.timeWeight,originalTime:i.originalTime})}}su(t,i){const n=Math.ceil(i/t);return null!==this.tr&&this.tr.eu===n||(this.tr={Ha:this.ru(n),eu:n}),this.tr.Ha}nu(t){if(0===t)return void this.J_.clear();const i=[];this.J_.forEach(((n,s)=>{t<=n[0].index?i.push(s):n.splice(Rt(n,t,(i=>i.index<t)),1/0)}));for(const t of i)this.J_.delete(t)}ru(t){let i=[];for(const n of Array.from(this.J_.keys()).sort(((t,i)=>i-t))){if(!this.J_.get(n))continue;const s=i;i=[];const e=s.length;let r=0;const h=d(this.J_.get(n)),l=h.length;let a=1/0,o=-1/0;for(let n=0;n<l;n++){const l=h[n],_=l.index;for(;r<e;){const t=s[r],n=t.index;if(!(n<_)){a=n;break}r++,i.push(t),o=n,a=1/0}if(a-_>=t&&_-o>=t)i.push(l),o=_;else if(this.Q_)return s}for(;r<e;r++)i.push(s[r])}return i}}class Mn{constructor(t){this.hu=t}lu(){return null===this.hu?null:new bn(Math.floor(this.hu.Bs()),Math.ceil(this.hu.ui()))}au(){return this.hu}static ou(){return new Mn(null)}}function xn(t,i){return t.weight>i.weight?t:i}class Sn{constructor(t,i,n,s){this.__=0,this._u=null,this.uu=[],this.Mo=null,this.wo=null,this.cu=new gn,this.du=new Map,this.fu=Mn.ou(),this.vu=!0,this.pu=new C,this.mu=new C,this.bu=new C,this.wu=null,this.gu=null,this.Mu=[],this.cn=i,this.yo=n,this.xu=i.rightOffset,this.Su=i.barSpacing,this.$i=t,this.q_=s,this.ku(),this.cu.tu(i.uniformDistribution)}W(){return this.cn}yu(t){T(this.yo,t),this.Cu(),this.ku()}$h(t,i){var n;T(this.cn,t),this.cn.fixLeftEdge&&this.Tu(),this.cn.fixRightEdge&&this.Pu(),void 0!==t.barSpacing&&this.$i.Gn(t.barSpacing),void 0!==t.rightOffset&&this.$i.Jn(t.rightOffset),void 0!==t.minBarSpacing&&this.$i.Gn(null!==(n=t.barSpacing)&&void 0!==n?n:this.Su),this.Cu(),this.ku(),this.bu.m()}mn(t){var i,n;return null!==(n=null===(i=this.uu[t])||void 0===i?void 0:i.time)&&void 0!==n?n:null}Ui(t){var i;return null!==(i=this.uu[t])&&void 0!==i?i:null}Oa(t,i){if(this.uu.length<1)return null;if(this.q_.key(t)>this.q_.key(this.uu[this.uu.length-1].time))return i?this.uu.length-1:null;const n=Rt(this.uu,this.q_.key(t),((t,i)=>this.q_.key(t.time)<i));return this.q_.key(t)<this.q_.key(this.uu[n].time)?i?n:null:n}Ni(){return 0===this.__||0===this.uu.length||null===this._u}Da(){return this.uu.length>0}Xs(){return this.Ru(),this.fu.lu()}Du(){return this.Ru(),this.fu.au()}Ou(){const t=this.Xs();if(null===t)return null;const i={from:t.Bs(),to:t.ui()};return this.Bu(i)}Bu(t){const i=Math.round(t.from),n=Math.round(t.to),s=f(this.Vu()),e=f(this.Au());return{from:f(this.Ui(Math.max(s,i))),to:f(this.Ui(Math.min(e,n)))}}zu(t){return{from:f(this.Oa(t.from,!0)),to:f(this.Oa(t.to,!0))}}Hi(){return this.__}S_(t){if(!isFinite(t)||t<=0)return;if(this.__===t)return;const i=this.Du(),n=this.__;if(this.__=t,this.vu=!0,this.cn.lockVisibleTimeRangeOnResize&&0!==n){const i=this.Su*t/n;this.Su=i}if(this.cn.fixLeftEdge&&null!==i&&i.Bs()<=0){const i=n-t;this.xu-=Math.round(i/this.Su)+1,this.vu=!0}this.Eu(),this.Iu()}zt(t){if(this.Ni()||!R(t))return 0;const i=this.Lu()+this.xu-t;return this.__-(i+.5)*this.Su-1}Qs(t,i){const n=this.Lu(),s=void 0===i?0:i.from,e=void 0===i?t.length:i.to;for(let i=s;i<e;i++){const s=t[i].ot,e=n+this.xu-s,r=this.__-(e+.5)*this.Su-1;t[i].nt=r}}Nu(t){return Math.ceil(this.Fu(t))}Jn(t){this.vu=!0,this.xu=t,this.Iu(),this.$i.Wu(),this.$i.Uh()}le(){return this.Su}Gn(t){this.ju(t),this.Iu(),this.$i.Wu(),this.$i.Uh()}Hu(){return this.xu}Ha(){if(this.Ni())return null;if(null!==this.gu)return this.gu;const t=this.Su,i=5*(this.$i.W().layout.fontSize+4)/8*(this.cn.tickMarkMaxCharacterLength||8),n=Math.round(i/t),s=f(this.Xs()),e=Math.max(s.Bs(),s.Bs()-n),r=Math.max(s.ui(),s.ui()-n),h=this.cu.su(t,i),l=this.Vu()+n,a=this.Au()-n,o=this.$u(),_=this.cn.fixLeftEdge||o,u=this.cn.fixRightEdge||o;let c=0;for(const t of h){if(!(e<=t.index&&t.index<=r))continue;let n;c<this.Mu.length?(n=this.Mu[c],n.coord=this.zt(t.index),n.label=this.Uu(t),n.weight=t.weight):(n={needAlignCoordinate:!1,coord:this.zt(t.index),label:this.Uu(t),weight:t.weight},this.Mu.push(n)),this.Su>i/2&&!o?n.needAlignCoordinate=!1:n.needAlignCoordinate=_&&t.index<=l||u&&t.index>=a,c++}return this.Mu.length=c,this.gu=this.Mu,this.Mu}qu(){this.vu=!0,this.Gn(this.cn.barSpacing),this.Jn(this.cn.rightOffset)}Yu(t){this.vu=!0,this._u=t,this.Iu(),this.Tu()}Zu(t,i){const n=this.Fu(t),s=this.le(),e=s+i*(s/10);this.Gn(e),this.cn.rightBarStaysOnScroll||this.Jn(this.Hu()+(n-this.Fu(t)))}Go(t){this.Mo&&this.n_(),null===this.wo&&null===this.wu&&(this.Ni()||(this.wo=t,this.Xu()))}Jo(t){if(null===this.wu)return;const i=gt(this.__-t,0,this.__),n=gt(this.__-f(this.wo),0,this.__);0!==i&&0!==n&&this.Gn(this.wu.le*i/n)}Qo(){null!==this.wo&&(this.wo=null,this.Ku())}t_(t){null===this.Mo&&null===this.wu&&(this.Ni()||(this.Mo=t,this.Xu()))}i_(t){if(null===this.Mo)return;const i=(this.Mo-t)/this.le();this.xu=f(this.wu).Hu+i,this.vu=!0,this.Iu()}n_(){null!==this.Mo&&(this.Mo=null,this.Ku())}Gu(){this.Ju(this.cn.rightOffset)}Ju(t,i=400){if(!isFinite(t))throw new RangeError(\"offset is required and must be finite number\");if(!isFinite(i)||i<=0)throw new RangeError(\"animationDuration (optional) must be finite positive number\");const n=this.xu,s=performance.now();this.$i.Zn({Qu:t=>(t-s)/i>=1,tc:e=>{const r=(e-s)/i;return r>=1?t:n+(t-n)*r}})}bt(t,i){this.vu=!0,this.uu=t,this.cu.iu(t,i),this.Iu()}nc(){return this.pu}sc(){return this.mu}ec(){return this.bu}Lu(){return this._u||0}rc(t){const i=t.G_();this.ju(this.__/i),this.xu=t.ui()-this.Lu(),this.Iu(),this.vu=!0,this.$i.Wu(),this.$i.Uh()}hc(){const t=this.Vu(),i=this.Au();null!==t&&null!==i&&this.rc(new bn(t,i+this.cn.rightOffset))}lc(t){const i=new bn(t.from,t.to);this.rc(i)}qi(t){return void 0!==this.yo.timeFormatter?this.yo.timeFormatter(t.originalTime):this.q_.formatHorzItem(t.time)}$u(){const{handleScroll:t,handleScale:i}=this.$i.W();return!(t.horzTouchDrag||t.mouseWheel||t.pressedMouseMove||t.vertTouchDrag||i.axisDoubleClickReset.time||i.axisPressedMouseMove.time||i.mouseWheel||i.pinch)}Vu(){return 0===this.uu.length?null:0}Au(){return 0===this.uu.length?null:this.uu.length-1}ac(t){return(this.__-1-t)/this.Su}Fu(t){const i=this.ac(t),n=this.Lu()+this.xu-i;return Math.round(1e6*n)/1e6}ju(t){const i=this.Su;this.Su=t,this.Eu(),i!==this.Su&&(this.vu=!0,this.oc())}Ru(){if(!this.vu)return;if(this.vu=!1,this.Ni())return void this._c(Mn.ou());const t=this.Lu(),i=this.__/this.Su,n=this.xu+t,s=new bn(n-i+1,n);this._c(new Mn(s))}Eu(){const t=this.uc();if(this.Su<t&&(this.Su=t,this.vu=!0),0!==this.__){const t=.5*this.__;this.Su>t&&(this.Su=t,this.vu=!0)}}uc(){return this.cn.fixLeftEdge&&this.cn.fixRightEdge&&0!==this.uu.length?this.__/this.uu.length:this.cn.minBarSpacing}Iu(){const t=this.cc();null!==t&&this.xu<t&&(this.xu=t,this.vu=!0);const i=this.dc();this.xu>i&&(this.xu=i,this.vu=!0)}cc(){const t=this.Vu(),i=this._u;if(null===t||null===i)return null;return t-i-1+(this.cn.fixLeftEdge?this.__/this.Su:Math.min(2,this.uu.length))}dc(){return this.cn.fixRightEdge?0:this.__/this.Su-Math.min(2,this.uu.length)}Xu(){this.wu={le:this.le(),Hu:this.Hu()}}Ku(){this.wu=null}Uu(t){let i=this.du.get(t.weight);return void 0===i&&(i=new mn((t=>this.fc(t)),this.q_),this.du.set(t.weight,i)),i.Y_(t)}fc(t){return this.q_.formatTickmark(t,this.yo)}_c(t){const i=this.fu;this.fu=t,wn(i.lu(),this.fu.lu())||this.pu.m(),wn(i.au(),this.fu.au())||this.mu.m(),this.oc()}oc(){this.gu=null}Cu(){this.oc(),this.du.clear()}ku(){this.q_.updateFormatter(this.yo)}Tu(){if(!this.cn.fixLeftEdge)return;const t=this.Vu();if(null===t)return;const i=this.Xs();if(null===i)return;const n=i.Bs()-t;if(n<0){const t=this.xu-n-1;this.Jn(t)}this.Eu()}Pu(){this.Iu(),this.Eu()}}class kn{X(t,i,n){t.useMediaCoordinateSpace((t=>this.K(t,i,n)))}gl(t,i,n){t.useMediaCoordinateSpace((t=>this.vc(t,i,n)))}vc(t,i,n){}}class yn extends kn{constructor(t){super(),this.mc=new Map,this.Et=t}K(t){}vc(t){if(!this.Et.yt)return;const{context:i,mediaSize:n}=t;let s=0;for(const t of this.Et.bc){if(0===t.Kt.length)continue;i.font=t.R;const e=this.wc(i,t.Kt);e>n.width?t.Zu=n.width/e:t.Zu=1,s+=t.gc*t.Zu}let e=0;switch(this.Et.Mc){case\"top\":e=0;break;case\"center\":e=Math.max((n.height-s)/2,0);break;case\"bottom\":e=Math.max(n.height-s,0)}i.fillStyle=this.Et.O;for(const t of this.Et.bc){i.save();let s=0;switch(this.Et.xc){case\"left\":i.textAlign=\"left\",s=t.gc/2;break;case\"center\":i.textAlign=\"center\",s=n.width/2;break;case\"right\":i.textAlign=\"right\",s=n.width-1-t.gc/2}i.translate(s,e),i.textBaseline=\"top\",i.font=t.R,i.scale(t.Zu,t.Zu),i.fillText(t.Kt,0,t.Sc),i.restore(),e+=t.gc*t.Zu}}wc(t,i){const n=this.kc(t.font);let s=n.get(i);return void 0===s&&(s=t.measureText(i).width,n.set(i,s)),s}kc(t){let i=this.mc.get(t);return void 0===i&&(i=new Map,this.mc.set(t,i)),i}}class Cn{constructor(t){this.ft=!0,this.Ft={yt:!1,O:\"\",bc:[],Mc:\"center\",xc:\"center\"},this.Wt=new yn(this.Ft),this.jt=t}bt(){this.ft=!0}gt(){return this.ft&&(this.Mt(),this.ft=!1),this.Wt}Mt(){const t=this.jt.W(),i=this.Ft;i.yt=t.visible,i.yt&&(i.O=t.color,i.xc=t.horzAlign,i.Mc=t.vertAlign,i.bc=[{Kt:t.text,R:E(t.fontSize,t.fontFamily,t.fontStyle),gc:1.2*t.fontSize,Sc:0,Zu:0}])}}class Tn extends st{constructor(t,i){super(),this.cn=i,this.wn=new Cn(this)}Rn(){return[]}Pn(){return[this.wn]}W(){return this.cn}On(){this.wn.bt()}}var Pn,Rn,Dn,On,Bn;!function(t){t[t.OnTouchEnd=0]=\"OnTouchEnd\",t[t.OnNextTap=1]=\"OnNextTap\"}(Pn||(Pn={}));class Vn{constructor(t,i,n){this.yc=[],this.Cc=[],this.__=0,this.Tc=null,this.Pc=new C,this.Rc=new C,this.Dc=null,this.Oc=t,this.cn=i,this.q_=n,this.Bc=new I(this),this.yl=new Sn(this,i.timeScale,this.cn.localization,n),this.vt=new rt(this,i.crosshair),this.Vc=new Zi(i.crosshair),this.Ac=new Tn(this,i.watermark),this.zc(),this.yc[0].x_(2e3),this.Ec=this.Ic(0),this.Lc=this.Ic(1)}Kl(){this.Nc(lt.es())}Uh(){this.Nc(lt.ss())}oa(){this.Nc(new lt(1))}Gl(t){const i=this.Fc(t);this.Nc(i)}Wc(){return this.Tc}jc(t){const i=this.Tc;this.Tc=t,null!==i&&this.Gl(i.Hc),null!==t&&this.Gl(t.Hc)}W(){return this.cn}$h(t){T(this.cn,t),this.yc.forEach((i=>i.b_(t))),void 0!==t.timeScale&&this.yl.$h(t.timeScale),void 0!==t.localization&&this.yl.yu(t.localization),(t.leftPriceScale||t.rightPriceScale)&&this.Pc.m(),this.Ec=this.Ic(0),this.Lc=this.Ic(1),this.Kl()}$c(t,i){if(\"left\"===t)return void this.$h({leftPriceScale:i});if(\"right\"===t)return void this.$h({rightPriceScale:i});const n=this.Uc(t);null!==n&&(n.Dt.$h(i),this.Pc.m())}Uc(t){for(const i of this.yc){const n=i.w_(t);if(null!==n)return{Ht:i,Dt:n}}return null}St(){return this.yl}qc(){return this.yc}Yc(){return this.Ac}Zc(){return this.vt}Xc(){return this.Rc}Kc(t,i){t.Io(i),this.Wu()}S_(t){this.__=t,this.yl.S_(this.__),this.yc.forEach((i=>i.S_(t))),this.Wu()}zc(t){const i=new pn(this.yl,this);void 0!==t?this.yc.splice(t,0,i):this.yc.push(i);const n=void 0===t?this.yc.length-1:t,s=lt.es();return s.Nn(n,{Fn:0,Wn:!0}),this.Nc(s),i}O_(t,i,n){t.O_(i,n)}B_(t,i,n){t.B_(i,n),this.Jl(),this.Nc(this.Gc(t,2))}V_(t,i){t.V_(i),this.Nc(this.Gc(t,2))}A_(t,i,n){i.Oo()||t.A_(i,n)}z_(t,i,n){i.Oo()||(t.z_(i,n),this.Jl(),this.Nc(this.Gc(t,2)))}E_(t,i){i.Oo()||(t.E_(i),this.Nc(this.Gc(t,2)))}L_(t,i){t.L_(i),this.Nc(this.Gc(t,2))}Jc(t){this.yl.Go(t)}Qc(t,i){const n=this.St();if(n.Ni()||0===i)return;const s=n.Hi();t=Math.max(1,Math.min(t,s)),n.Zu(t,i),this.Wu()}td(t){this.nd(0),this.sd(t),this.ed()}rd(t){this.yl.Jo(t),this.Wu()}hd(){this.yl.Qo(),this.Uh()}nd(t){this.yl.t_(t)}sd(t){this.yl.i_(t),this.Wu()}ed(){this.yl.n_(),this.Uh()}wt(){return this.Cc}ld(t,i,n,s,e){this.vt.gn(t,i);let r=NaN,h=this.yl.Nu(t);const l=this.yl.Xs();null!==l&&(h=Math.min(Math.max(l.Bs(),h),l.ui()));const a=s.vn(),o=a.Ct();null!==o&&(r=a.pn(i,o)),r=this.Vc.Ba(r,h,s),this.vt.kn(h,r,s),this.oa(),e||this.Rc.m(this.vt.xt(),{x:t,y:i},n)}ad(t,i,n){const s=n.vn(),e=s.Ct(),r=s.Rt(t,f(e)),h=this.yl.Oa(i,!0),l=this.yl.zt(f(h));this.ld(l,r,null,n,!0)}od(t){this.Zc().Cn(),this.oa(),t||this.Rc.m(null,null,null)}Jl(){const t=this.vt.Ht();if(null!==t){const i=this.vt.xn(),n=this.vt.Sn();this.ld(i,n,null,t)}this.vt.On()}_d(t,i,n){const s=this.yl.mn(0);void 0!==i&&void 0!==n&&this.yl.bt(i,n);const e=this.yl.mn(0),r=this.yl.Lu(),h=this.yl.Xs();if(null!==h&&null!==s&&null!==e){const i=h.Kr(r),l=this.q_.key(s)>this.q_.key(e),a=null!==t&&t>r&&!l,o=this.yl.W().allowShiftVisibleRangeOnWhitespaceReplacement,_=i&&(!(void 0===n)||o)&&this.yl.W().shiftVisibleRangeOnNewBar;if(a&&!_){const i=t-r;this.yl.Jn(this.yl.Hu()-i)}}this.yl.Yu(t)}ia(t){null!==t&&t.F_()}dr(t){const i=this.yc.find((i=>i.Uo().includes(t)));return void 0===i?null:i}Wu(){this.Ac.On(),this.yc.forEach((t=>t.F_())),this.Jl()}S(){this.yc.forEach((t=>t.S())),this.yc.length=0,this.cn.localization.priceFormatter=void 0,this.cn.localization.percentageFormatter=void 0,this.cn.localization.timeFormatter=void 0}ud(){return this.Bc}br(){return this.Bc.W()}g_(){return this.Pc}dd(t,i,n){const s=this.yc[0],e=this.fd(i,t,s,n);return this.Cc.push(e),1===this.Cc.length?this.Kl():this.Uh(),e}vd(t){const i=this.dr(t),n=this.Cc.indexOf(t);c(-1!==n,\"Series not found\"),this.Cc.splice(n,1),f(i).Zo(t),t.S&&t.S()}Xl(t,i){const n=f(this.dr(t));n.Zo(t);const s=this.Uc(i);if(null===s){const s=t.Xi();n.qo(t,i,s)}else{const e=s.Ht===n?t.Xi():void 0;s.Ht.qo(t,i,e)}}hc(){const t=lt.ss();t.$n(),this.Nc(t)}pd(t){const i=lt.ss();i.Yn(t),this.Nc(i)}Kn(){const t=lt.ss();t.Kn(),this.Nc(t)}Gn(t){const i=lt.ss();i.Gn(t),this.Nc(i)}Jn(t){const i=lt.ss();i.Jn(t),this.Nc(i)}Zn(t){const i=lt.ss();i.Zn(t),this.Nc(i)}Un(){const t=lt.ss();t.Un(),this.Nc(t)}md(){return this.cn.rightPriceScale.visible?\"right\":\"left\"}bd(){return this.Lc}q(){return this.Ec}Vt(t){const i=this.Lc,n=this.Ec;if(i===n)return i;if(t=Math.max(0,Math.min(100,Math.round(100*t))),null===this.Dc||this.Dc.Ps!==n||this.Dc.Rs!==i)this.Dc={Ps:n,Rs:i,wd:new Map};else{const i=this.Dc.wd.get(t);if(void 0!==i)return i}const s=function(t,i,n){const[s,e,r,h]=S(t),[l,a,o,_]=S(i),u=[m(s+n*(l-s)),m(e+n*(a-e)),m(r+n*(o-r)),b(h+n*(_-h))];return`rgba(${u[0]}, ${u[1]}, ${u[2]}, ${u[3]})`}(n,i,t/100);return this.Dc.wd.set(t,s),s}Gc(t,i){const n=new lt(i);if(null!==t){const s=this.yc.indexOf(t);n.Nn(s,{Fn:i})}return n}Fc(t,i){return void 0===i&&(i=2),this.Gc(this.dr(t),i)}Nc(t){this.Oc&&this.Oc(t),this.yc.forEach((t=>t.j_().qh().bt()))}fd(t,i,n,s){const e=new Yi(this,t,i,n,s),r=void 0!==t.priceScaleId?t.priceScaleId:this.md();return n.qo(e,r),ht(r)||e.$h(t),e}Ic(t){const i=this.cn.layout;return\"gradient\"===i.background.type?0===t?i.background.topColor:i.background.bottomColor:i.background.color}}function An(t){return!P(t)&&!D(t)}function zn(t){return P(t)}!function(t){t[t.Disabled=0]=\"Disabled\",t[t.Continuous=1]=\"Continuous\",t[t.OnDataUpdate=2]=\"OnDataUpdate\"}(Rn||(Rn={})),function(t){t[t.LastBar=0]=\"LastBar\",t[t.LastVisible=1]=\"LastVisible\"}(Dn||(Dn={})),function(t){t.Solid=\"solid\",t.VerticalGradient=\"gradient\"}(On||(On={})),function(t){t[t.Year=0]=\"Year\",t[t.Month=1]=\"Month\",t[t.DayOfMonth=2]=\"DayOfMonth\",t[t.Time=3]=\"Time\",t[t.TimeWithSeconds=4]=\"TimeWithSeconds\"}(Bn||(Bn={}));const En=t=>t.getUTCFullYear();function In(t,i,n){return i.replace(/yyyy/g,(t=>ot(En(t),4))(t)).replace(/yy/g,(t=>ot(En(t)%100,2))(t)).replace(/MMMM/g,((t,i)=>new Date(t.getUTCFullYear(),t.getUTCMonth(),1).toLocaleString(i,{month:\"long\"}))(t,n)).replace(/MMM/g,((t,i)=>new Date(t.getUTCFullYear(),t.getUTCMonth(),1).toLocaleString(i,{month:\"short\"}))(t,n)).replace(/MM/g,(t=>ot((t=>t.getUTCMonth()+1)(t),2))(t)).replace(/dd/g,(t=>ot((t=>t.getUTCDate())(t),2))(t))}class Ln{constructor(t=\"yyyy-MM-dd\",i=\"default\"){this.gd=t,this.Md=i}Y_(t){return In(t,this.gd,this.Md)}}class Nn{constructor(t){this.xd=t||\"%h:%m:%s\"}Y_(t){return this.xd.replace(\"%h\",ot(t.getUTCHours(),2)).replace(\"%m\",ot(t.getUTCMinutes(),2)).replace(\"%s\",ot(t.getUTCSeconds(),2))}}const Fn={Sd:\"yyyy-MM-dd\",kd:\"%h:%m:%s\",yd:\" \",Cd:\"default\"};class Wn{constructor(t={}){const i=Object.assign(Object.assign({},Fn),t);this.Td=new Ln(i.Sd,i.Cd),this.Pd=new Nn(i.kd),this.Rd=i.yd}Y_(t){return`${this.Td.Y_(t)}${this.Rd}${this.Pd.Y_(t)}`}}function jn(t){return 60*t*60*1e3}function Hn(t){return 60*t*1e3}const $n=[{Dd:(Un=1,1e3*Un),Od:10},{Dd:Hn(1),Od:20},{Dd:Hn(5),Od:21},{Dd:Hn(30),Od:22},{Dd:jn(1),Od:30},{Dd:jn(3),Od:31},{Dd:jn(6),Od:32},{Dd:jn(12),Od:33}];var Un;function qn(t,i){if(t.getUTCFullYear()!==i.getUTCFullYear())return 70;if(t.getUTCMonth()!==i.getUTCMonth())return 60;if(t.getUTCDate()!==i.getUTCDate())return 50;for(let n=$n.length-1;n>=0;--n)if(Math.floor(i.getTime()/$n[n].Dd)!==Math.floor(t.getTime()/$n[n].Dd))return $n[n].Od;return 0}function Yn(t){let i=t;if(D(t)&&(i=Xn(t)),!An(i))throw new Error(\"time must be of type BusinessDay\");const n=new Date(Date.UTC(i.year,i.month-1,i.day,0,0,0,0));return{Bd:Math.round(n.getTime()/1e3),Vd:i}}function Zn(t){if(!zn(t))throw new Error(\"time must be of type isUTCTimestamp\");return{Bd:t}}function Xn(t){const i=new Date(t);if(isNaN(i.getTime()))throw new Error(`Invalid date string=${t}, expected format=yyyy-mm-dd`);return{day:i.getUTCDate(),month:i.getUTCMonth()+1,year:i.getUTCFullYear()}}function Kn(t){D(t.time)&&(t.time=Xn(t.time))}class Gn{options(){return this.cn}setOptions(t){this.cn=t,this.updateFormatter(t.localization)}preprocessData(t){Array.isArray(t)?function(t){t.forEach(Kn)}(t):Kn(t)}createConverterToInternalObj(t){return f(function(t){return 0===t.length?null:An(t[0].time)||D(t[0].time)?Yn:Zn}(t))}key(t){return\"object\"==typeof t&&\"Bd\"in t?t.Bd:this.key(this.convertHorzItemToInternal(t))}cacheKey(t){const i=t;return void 0===i.Vd?new Date(1e3*i.Bd).getTime():new Date(Date.UTC(i.Vd.year,i.Vd.month-1,i.Vd.day)).getTime()}convertHorzItemToInternal(t){return zn(i=t)?Zn(i):An(i)?Yn(i):Yn(Xn(i));var i}updateFormatter(t){if(!this.cn)return;const i=t.dateFormat;this.cn.timeScale.timeVisible?this.Ad=new Wn({Sd:i,kd:this.cn.timeScale.secondsVisible?\"%h:%m:%s\":\"%h:%m\",yd:\"   \",Cd:t.locale}):this.Ad=new Ln(i,t.locale)}formatHorzItem(t){const i=t;return this.Ad.Y_(new Date(1e3*i.Bd))}formatTickmark(t,i){const n=function(t,i,n){switch(t){case 0:case 10:return i?n?4:3:2;case 20:case 21:case 22:case 30:case 31:case 32:case 33:return i?3:2;case 50:return 2;case 60:return 1;case 70:return 0}}(t.weight,this.cn.timeScale.timeVisible,this.cn.timeScale.secondsVisible),s=this.cn.timeScale;if(void 0!==s.tickMarkFormatter){const e=s.tickMarkFormatter(t.originalTime,n,i.locale);if(null!==e)return e}return function(t,i,n){const s={};switch(i){case 0:s.year=\"numeric\";break;case 1:s.month=\"short\";break;case 2:s.day=\"numeric\";break;case 3:s.hour12=!1,s.hour=\"2-digit\",s.minute=\"2-digit\";break;case 4:s.hour12=!1,s.hour=\"2-digit\",s.minute=\"2-digit\",s.second=\"2-digit\"}const e=void 0===t.Vd?new Date(1e3*t.Bd):new Date(Date.UTC(t.Vd.year,t.Vd.month-1,t.Vd.day));return new Date(e.getUTCFullYear(),e.getUTCMonth(),e.getUTCDate(),e.getUTCHours(),e.getUTCMinutes(),e.getUTCSeconds(),e.getUTCMilliseconds()).toLocaleString(n,s)}(t.time,n,i.locale)}maxTickMarkWeight(t){let i=t.reduce(xn,t[0]).weight;return i>30&&i<50&&(i=30),i}fillWeightsForPoints(t,i){!function(t,i=0){if(0===t.length)return;let n=0===i?null:t[i-1].time.Bd,s=null!==n?new Date(1e3*n):null,e=0;for(let r=i;r<t.length;++r){const i=t[r],h=new Date(1e3*i.time.Bd);null!==s&&(i.timeWeight=qn(h,s)),e+=i.time.Bd-(n||i.time.Bd),n=i.time.Bd,s=h}if(0===i&&t.length>1){const i=Math.ceil(e/(t.length-1)),n=new Date(1e3*(t[0].time.Bd-i));t[0].timeWeight=qn(new Date(1e3*t[0].time.Bd),n)}}(t,i)}static zd(t){return T({localization:{dateFormat:\"dd MMM 'yy\"}},null!=t?t:{})}}function Jn(t){var i=t.width,n=t.height;if(i<0)throw new Error(\"Negative width is not allowed for Size\");if(n<0)throw new Error(\"Negative height is not allowed for Size\");return{width:i,height:n}}function Qn(t,i){return t.width===i.width&&t.height===i.height}var ts=function(){function t(t){var i=this;this._resolutionListener=function(){return i._onResolutionChanged()},this._resolutionMediaQueryList=null,this._observers=[],this._window=t,this._installResolutionListener()}return t.prototype.dispose=function(){this._uninstallResolutionListener(),this._window=null},Object.defineProperty(t.prototype,\"value\",{get:function(){return this._window.devicePixelRatio},enumerable:!1,configurable:!0}),t.prototype.subscribe=function(t){var i=this,n={next:t};return this._observers.push(n),{unsubscribe:function(){i._observers=i._observers.filter((function(t){return t!==n}))}}},t.prototype._installResolutionListener=function(){if(null!==this._resolutionMediaQueryList)throw new Error(\"Resolution listener is already installed\");var t=this._window.devicePixelRatio;this._resolutionMediaQueryList=this._window.matchMedia(\"all and (resolution: \".concat(t,\"dppx)\")),this._resolutionMediaQueryList.addListener(this._resolutionListener)},t.prototype._uninstallResolutionListener=function(){null!==this._resolutionMediaQueryList&&(this._resolutionMediaQueryList.removeListener(this._resolutionListener),this._resolutionMediaQueryList=null)},t.prototype._reinstallResolutionListener=function(){this._uninstallResolutionListener(),this._installResolutionListener()},t.prototype._onResolutionChanged=function(){var t=this;this._observers.forEach((function(i){return i.next(t._window.devicePixelRatio)})),this._reinstallResolutionListener()},t}();var is=function(){function t(t,i,n){var s;this._canvasElement=null,this._bitmapSizeChangedListeners=[],this._suggestedBitmapSize=null,this._suggestedBitmapSizeChangedListeners=[],this._devicePixelRatioObservable=null,this._canvasElementResizeObserver=null,this._canvasElement=t,this._canvasElementClientSize=Jn({width:this._canvasElement.clientWidth,height:this._canvasElement.clientHeight}),this._transformBitmapSize=null!=i?i:function(t){return t},this._allowResizeObserver=null===(s=null==n?void 0:n.allowResizeObserver)||void 0===s||s,this._chooseAndInitObserver()}return t.prototype.dispose=function(){var t,i;if(null===this._canvasElement)throw new Error(\"Object is disposed\");null===(t=this._canvasElementResizeObserver)||void 0===t||t.disconnect(),this._canvasElementResizeObserver=null,null===(i=this._devicePixelRatioObservable)||void 0===i||i.dispose(),this._devicePixelRatioObservable=null,this._suggestedBitmapSizeChangedListeners.length=0,this._bitmapSizeChangedListeners.length=0,this._canvasElement=null},Object.defineProperty(t.prototype,\"canvasElement\",{get:function(){if(null===this._canvasElement)throw new Error(\"Object is disposed\");return this._canvasElement},enumerable:!1,configurable:!0}),Object.defineProperty(t.prototype,\"canvasElementClientSize\",{get:function(){return this._canvasElementClientSize},enumerable:!1,configurable:!0}),Object.defineProperty(t.prototype,\"bitmapSize\",{get:function(){return Jn({width:this.canvasElement.width,height:this.canvasElement.height})},enumerable:!1,configurable:!0}),t.prototype.resizeCanvasElement=function(t){this._canvasElementClientSize=Jn(t),this.canvasElement.style.width=\"\".concat(this._canvasElementClientSize.width,\"px\"),this.canvasElement.style.height=\"\".concat(this._canvasElementClientSize.height,\"px\"),this._invalidateBitmapSize()},t.prototype.subscribeBitmapSizeChanged=function(t){this._bitmapSizeChangedListeners.push(t)},t.prototype.unsubscribeBitmapSizeChanged=function(t){this._bitmapSizeChangedListeners=this._bitmapSizeChangedListeners.filter((function(i){return i!==t}))},Object.defineProperty(t.prototype,\"suggestedBitmapSize\",{get:function(){return this._suggestedBitmapSize},enumerable:!1,configurable:!0}),t.prototype.subscribeSuggestedBitmapSizeChanged=function(t){this._suggestedBitmapSizeChangedListeners.push(t)},t.prototype.unsubscribeSuggestedBitmapSizeChanged=function(t){this._suggestedBitmapSizeChangedListeners=this._suggestedBitmapSizeChangedListeners.filter((function(i){return i!==t}))},t.prototype.applySuggestedBitmapSize=function(){if(null!==this._suggestedBitmapSize){var t=this._suggestedBitmapSize;this._suggestedBitmapSize=null,this._resizeBitmap(t),this._emitSuggestedBitmapSizeChanged(t,this._suggestedBitmapSize)}},t.prototype._resizeBitmap=function(t){var i=this.bitmapSize;Qn(i,t)||(this.canvasElement.width=t.width,this.canvasElement.height=t.height,this._emitBitmapSizeChanged(i,t))},t.prototype._emitBitmapSizeChanged=function(t,i){var n=this;this._bitmapSizeChangedListeners.forEach((function(s){return s.call(n,t,i)}))},t.prototype._suggestNewBitmapSize=function(t){var i=this._suggestedBitmapSize,n=Jn(this._transformBitmapSize(t,this._canvasElementClientSize)),s=Qn(this.bitmapSize,n)?null:n;null===i&&null===s||null!==i&&null!==s&&Qn(i,s)||(this._suggestedBitmapSize=s,this._emitSuggestedBitmapSizeChanged(i,s))},t.prototype._emitSuggestedBitmapSizeChanged=function(t,i){var n=this;this._suggestedBitmapSizeChangedListeners.forEach((function(s){return s.call(n,t,i)}))},t.prototype._chooseAndInitObserver=function(){var t=this;this._allowResizeObserver?new Promise((function(t){var i=new ResizeObserver((function(n){t(n.every((function(t){return\"devicePixelContentBoxSize\"in t}))),i.disconnect()}));i.observe(document.body,{box:\"device-pixel-content-box\"})})).catch((function(){return!1})).then((function(i){return i?t._initResizeObserver():t._initDevicePixelRatioObservable()})):this._initDevicePixelRatioObservable()},t.prototype._initDevicePixelRatioObservable=function(){var t=this;if(null!==this._canvasElement){var i=ns(this._canvasElement);if(null===i)throw new Error(\"No window is associated with the canvas\");this._devicePixelRatioObservable=function(t){return new ts(t)}(i),this._devicePixelRatioObservable.subscribe((function(){return t._invalidateBitmapSize()})),this._invalidateBitmapSize()}},t.prototype._invalidateBitmapSize=function(){var t,i;if(null!==this._canvasElement){var n=ns(this._canvasElement);if(null!==n){var s=null!==(i=null===(t=this._devicePixelRatioObservable)||void 0===t?void 0:t.value)&&void 0!==i?i:n.devicePixelRatio,e=this._canvasElement.getClientRects(),r=void 0!==e[0]?function(t,i){return Jn({width:Math.round(t.left*i+t.width*i)-Math.round(t.left*i),height:Math.round(t.top*i+t.height*i)-Math.round(t.top*i)})}(e[0],s):Jn({width:this._canvasElementClientSize.width*s,height:this._canvasElementClientSize.height*s});this._suggestNewBitmapSize(r)}}},t.prototype._initResizeObserver=function(){var t=this;null!==this._canvasElement&&(this._canvasElementResizeObserver=new ResizeObserver((function(i){var n=i.find((function(i){return i.target===t._canvasElement}));if(n&&n.devicePixelContentBoxSize&&n.devicePixelContentBoxSize[0]){var s=n.devicePixelContentBoxSize[0],e=Jn({width:s.inlineSize,height:s.blockSize});t._suggestNewBitmapSize(e)}})),this._canvasElementResizeObserver.observe(this._canvasElement,{box:\"device-pixel-content-box\"}))},t}();function ns(t){return t.ownerDocument.defaultView}var ss=function(){function t(t,i,n){if(0===i.width||0===i.height)throw new TypeError(\"Rendering target could only be created on a media with positive width and height\");if(this._mediaSize=i,0===n.width||0===n.height)throw new TypeError(\"Rendering target could only be created using a bitmap with positive integer width and height\");this._bitmapSize=n,this._context=t}return t.prototype.useMediaCoordinateSpace=function(t){try{return this._context.save(),this._context.setTransform(1,0,0,1,0,0),this._context.scale(this._horizontalPixelRatio,this._verticalPixelRatio),t({context:this._context,mediaSize:this._mediaSize})}finally{this._context.restore()}},t.prototype.useBitmapCoordinateSpace=function(t){try{return this._context.save(),this._context.setTransform(1,0,0,1,0,0),t({context:this._context,mediaSize:this._mediaSize,bitmapSize:this._bitmapSize,horizontalPixelRatio:this._horizontalPixelRatio,verticalPixelRatio:this._verticalPixelRatio})}finally{this._context.restore()}},Object.defineProperty(t.prototype,\"_horizontalPixelRatio\",{get:function(){return this._bitmapSize.width/this._mediaSize.width},enumerable:!1,configurable:!0}),Object.defineProperty(t.prototype,\"_verticalPixelRatio\",{get:function(){return this._bitmapSize.height/this._mediaSize.height},enumerable:!1,configurable:!0}),t}();function es(t,i){var n=t.canvasElementClientSize;if(0===n.width||0===n.height)return null;var s=t.bitmapSize;if(0===s.width||0===s.height)return null;var e=t.canvasElement.getContext(\"2d\",i);return null===e?null:new ss(e,n,s)}const rs=\"undefined\"!=typeof window;function hs(){return!!rs&&window.navigator.userAgent.toLowerCase().indexOf(\"firefox\")>-1}function ls(){return!!rs&&/iPhone|iPad|iPod/.test(window.navigator.platform)}function as(t){return t+t%2}function os(t,i){return t.Ed-i.Ed}function _s(t,i,n){const s=(t.Ed-i.Ed)/(t.ot-i.ot);return Math.sign(s)*Math.min(Math.abs(s),n)}class us{constructor(t,i,n,s){this.Id=null,this.Ld=null,this.Nd=null,this.Fd=null,this.Wd=null,this.jd=0,this.Hd=0,this.$d=t,this.Ud=i,this.qd=n,this.rs=s}Yd(t,i){if(null!==this.Id){if(this.Id.ot===i)return void(this.Id.Ed=t);if(Math.abs(this.Id.Ed-t)<this.rs)return}this.Fd=this.Nd,this.Nd=this.Ld,this.Ld=this.Id,this.Id={ot:i,Ed:t}}Or(t,i){if(null===this.Id||null===this.Ld)return;if(i-this.Id.ot>50)return;let n=0;const s=_s(this.Id,this.Ld,this.Ud),e=os(this.Id,this.Ld),r=[s],h=[e];if(n+=e,null!==this.Nd){const t=_s(this.Ld,this.Nd,this.Ud);if(Math.sign(t)===Math.sign(s)){const i=os(this.Ld,this.Nd);if(r.push(t),h.push(i),n+=i,null!==this.Fd){const t=_s(this.Nd,this.Fd,this.Ud);if(Math.sign(t)===Math.sign(s)){const i=os(this.Nd,this.Fd);r.push(t),h.push(i),n+=i}}}}let l=0;for(let t=0;t<r.length;++t)l+=h[t]/n*r[t];Math.abs(l)<this.$d||(this.Wd={Ed:t,ot:i},this.Hd=l,this.jd=function(t,i){const n=Math.log(i);return Math.log(1*n/-t)/n}(Math.abs(l),this.qd))}tc(t){const i=f(this.Wd),n=t-i.ot;return i.Ed+this.Hd*(Math.pow(this.qd,n)-1)/Math.log(this.qd)}Qu(t){return null===this.Wd||this.Zd(t)===this.jd}Zd(t){const i=t-f(this.Wd).ot;return Math.min(i,this.jd)}}class cs{constructor(t,i){this.Xd=void 0,this.Kd=void 0,this.Gd=void 0,this.en=!1,this.Jd=t,this.Qd=i,this.tf()}bt(){this.tf()}if(){this.Xd&&this.Jd.removeChild(this.Xd),this.Kd&&this.Jd.removeChild(this.Kd),this.Xd=void 0,this.Kd=void 0}nf(){return this.en!==this.sf()||this.Gd!==this.ef()}ef(){return k(S(this.Qd.W().layout.textColor))>160?\"dark\":\"light\"}sf(){return this.Qd.W().layout.attributionLogo}rf(){const t=new URL(location.href);return t.hostname?\"&utm_source=\"+t.hostname+t.pathname:\"\"}tf(){this.nf()&&(this.if(),this.en=this.sf(),this.en&&(this.Gd=this.ef(),this.Kd=document.createElement(\"style\"),this.Kd.innerText=\"a#tv-attr-logo{--fill:#131722;--stroke:#fff;position:absolute;left:10px;bottom:10px;height:19px;width:35px;margin:0;padding:0;border:0;z-index:3;}a#tv-attr-logo[data-dark]{--fill:#D1D4DC;--stroke:#131722;}\",this.Xd=document.createElement(\"a\"),this.Xd.href=`https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart${this.rf()}`,this.Xd.title=\"Charting by TradingView\",this.Xd.id=\"tv-attr-logo\",this.Xd.target=\"_blank\",this.Xd.innerHTML='<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 35 19\" width=\"35\" height=\"19\" fill=\"none\"><g fill-rule=\"evenodd\" clip-path=\"url(#a)\" clip-rule=\"evenodd\"><path fill=\"var(--stroke)\" d=\"M2 0H0v10h6v9h21.4l.5-1.3 6-15 1-2.7H23.7l-.5 1.3-.2.6a5 5 0 0 0-7-.9V0H2Zm20 17h4l5.2-13 .8-2h-7l-1 2.5-.2.5-1.5 3.8-.3.7V17Zm-.8-10a3 3 0 0 0 .7-2.7A3 3 0 1 0 16.8 7h4.4ZM14 7V2H2v6h6v9h4V7h2Z\"/><path fill=\"var(--fill)\" d=\"M14 2H2v6h6v9h6V2Zm12 15h-7l6-15h7l-6 15Zm-7-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z\"/></g><defs><clipPath id=\"a\"><path fill=\"var(--stroke)\" d=\"M0 0h35v19H0z\"/></clipPath></defs></svg>',this.Xd.toggleAttribute(\"data-dark\",\"dark\"===this.Gd),this.Jd.appendChild(this.Kd),this.Jd.appendChild(this.Xd)))}}function ds(t,i){const n=f(t.ownerDocument).createElement(\"canvas\");t.appendChild(n);const s=function(t,i){if(\"device-pixel-content-box\"===i.type)return new is(t,i.transform,i.options);throw new Error(\"Unsupported binding target\")}(n,{type:\"device-pixel-content-box\",options:{allowResizeObserver:!1},transform:(t,i)=>({width:Math.max(t.width,i.width),height:Math.max(t.height,i.height)})});return s.resizeCanvasElement(i),s}function fs(t){var i;t.width=1,t.height=1,null===(i=t.getContext(\"2d\"))||void 0===i||i.clearRect(0,0,1,1)}function vs(t,i,n,s){t.gl&&t.gl(i,n,s)}function ps(t,i,n,s){t.X(i,n,s)}function ms(t,i,n,s){const e=t(n,s);for(const t of e){const n=t.gt();null!==n&&i(n)}}function bs(t){rs&&void 0!==window.chrome&&t.addEventListener(\"mousedown\",(t=>{if(1===t.button)return t.preventDefault(),!1}))}class ws{constructor(t,i,n){this.hf=0,this.lf=null,this.af={nt:Number.NEGATIVE_INFINITY,st:Number.POSITIVE_INFINITY},this._f=0,this.uf=null,this.cf={nt:Number.NEGATIVE_INFINITY,st:Number.POSITIVE_INFINITY},this.df=null,this.ff=!1,this.vf=null,this.pf=null,this.mf=!1,this.bf=!1,this.wf=!1,this.gf=null,this.Mf=null,this.xf=null,this.Sf=null,this.kf=null,this.yf=null,this.Cf=null,this.Tf=0,this.Pf=!1,this.Rf=!1,this.Df=!1,this.Of=0,this.Bf=null,this.Vf=!ls(),this.Af=t=>{this.zf(t)},this.Ef=t=>{if(this.If(t)){const i=this.Lf(t);if(++this._f,this.uf&&this._f>1){const{Nf:n}=this.Ff(xs(t),this.cf);n<30&&!this.wf&&this.Wf(i,this.Hf.jf),this.$f()}}else{const i=this.Lf(t);if(++this.hf,this.lf&&this.hf>1){const{Nf:n}=this.Ff(xs(t),this.af);n<5&&!this.bf&&this.Uf(i,this.Hf.qf),this.Yf()}}},this.Zf=t,this.Hf=i,this.cn=n,this.Xf()}S(){null!==this.gf&&(this.gf(),this.gf=null),null!==this.Mf&&(this.Mf(),this.Mf=null),null!==this.Sf&&(this.Sf(),this.Sf=null),null!==this.kf&&(this.kf(),this.kf=null),null!==this.yf&&(this.yf(),this.yf=null),null!==this.xf&&(this.xf(),this.xf=null),this.Kf(),this.Yf()}Gf(t){this.Sf&&this.Sf();const i=this.Jf.bind(this);if(this.Sf=()=>{this.Zf.removeEventListener(\"mousemove\",i)},this.Zf.addEventListener(\"mousemove\",i),this.If(t))return;const n=this.Lf(t);this.Uf(n,this.Hf.Qf),this.Vf=!0}Yf(){null!==this.lf&&clearTimeout(this.lf),this.hf=0,this.lf=null,this.af={nt:Number.NEGATIVE_INFINITY,st:Number.POSITIVE_INFINITY}}$f(){null!==this.uf&&clearTimeout(this.uf),this._f=0,this.uf=null,this.cf={nt:Number.NEGATIVE_INFINITY,st:Number.POSITIVE_INFINITY}}Jf(t){if(this.Df||null!==this.pf)return;if(this.If(t))return;const i=this.Lf(t);this.Uf(i,this.Hf.tv),this.Vf=!0}iv(t){const i=ks(t.changedTouches,f(this.Bf));if(null===i)return;if(this.Of=Ss(t),null!==this.Cf)return;if(this.Rf)return;this.Pf=!0;const n=this.Ff(xs(i),f(this.pf)),{nv:s,sv:e,Nf:r}=n;if(this.mf||!(r<5)){if(!this.mf){const t=.5*s,i=e>=t&&!this.cn.ev(),n=t>e&&!this.cn.rv();i||n||(this.Rf=!0),this.mf=!0,this.wf=!0,this.Kf(),this.$f()}if(!this.Rf){const n=this.Lf(t,i);this.Wf(n,this.Hf.hv),Ms(t)}}}lv(t){if(0!==t.button)return;const i=this.Ff(xs(t),f(this.vf)),{Nf:n}=i;if(n>=5&&(this.bf=!0,this.Yf()),this.bf){const i=this.Lf(t);this.Uf(i,this.Hf.av)}}Ff(t,i){const n=Math.abs(i.nt-t.nt),s=Math.abs(i.st-t.st);return{nv:n,sv:s,Nf:n+s}}ov(t){let i=ks(t.changedTouches,f(this.Bf));if(null===i&&0===t.touches.length&&(i=t.changedTouches[0]),null===i)return;this.Bf=null,this.Of=Ss(t),this.Kf(),this.pf=null,this.yf&&(this.yf(),this.yf=null);const n=this.Lf(t,i);if(this.Wf(n,this.Hf._v),++this._f,this.uf&&this._f>1){const{Nf:t}=this.Ff(xs(i),this.cf);t<30&&!this.wf&&this.Wf(n,this.Hf.jf),this.$f()}else this.wf||(this.Wf(n,this.Hf.uv),this.Hf.uv&&Ms(t));0===this._f&&Ms(t),0===t.touches.length&&this.ff&&(this.ff=!1,Ms(t))}zf(t){if(0!==t.button)return;const i=this.Lf(t);if(this.vf=null,this.Df=!1,this.kf&&(this.kf(),this.kf=null),hs()){this.Zf.ownerDocument.documentElement.removeEventListener(\"mouseleave\",this.Af)}if(!this.If(t))if(this.Uf(i,this.Hf.cv),++this.hf,this.lf&&this.hf>1){const{Nf:n}=this.Ff(xs(t),this.af);n<5&&!this.bf&&this.Uf(i,this.Hf.qf),this.Yf()}else this.bf||this.Uf(i,this.Hf.dv)}Kf(){null!==this.df&&(clearTimeout(this.df),this.df=null)}fv(t){if(null!==this.Bf)return;const i=t.changedTouches[0];this.Bf=i.identifier,this.Of=Ss(t);const n=this.Zf.ownerDocument.documentElement;this.wf=!1,this.mf=!1,this.Rf=!1,this.pf=xs(i),this.yf&&(this.yf(),this.yf=null);{const i=this.iv.bind(this),s=this.ov.bind(this);this.yf=()=>{n.removeEventListener(\"touchmove\",i),n.removeEventListener(\"touchend\",s)},n.addEventListener(\"touchmove\",i,{passive:!1}),n.addEventListener(\"touchend\",s,{passive:!1}),this.Kf(),this.df=setTimeout(this.vv.bind(this,t),240)}const s=this.Lf(t,i);this.Wf(s,this.Hf.pv),this.uf||(this._f=0,this.uf=setTimeout(this.$f.bind(this),500),this.cf=xs(i))}mv(t){if(0!==t.button)return;const i=this.Zf.ownerDocument.documentElement;hs()&&i.addEventListener(\"mouseleave\",this.Af),this.bf=!1,this.vf=xs(t),this.kf&&(this.kf(),this.kf=null);{const t=this.lv.bind(this),n=this.zf.bind(this);this.kf=()=>{i.removeEventListener(\"mousemove\",t),i.removeEventListener(\"mouseup\",n)},i.addEventListener(\"mousemove\",t),i.addEventListener(\"mouseup\",n)}if(this.Df=!0,this.If(t))return;const n=this.Lf(t);this.Uf(n,this.Hf.bv),this.lf||(this.hf=0,this.lf=setTimeout(this.Yf.bind(this),500),this.af=xs(t))}Xf(){this.Zf.addEventListener(\"mouseenter\",this.Gf.bind(this)),this.Zf.addEventListener(\"touchcancel\",this.Kf.bind(this));{const t=this.Zf.ownerDocument,i=t=>{this.Hf.wv&&(t.composed&&this.Zf.contains(t.composedPath()[0])||t.target&&this.Zf.contains(t.target)||this.Hf.wv())};this.Mf=()=>{t.removeEventListener(\"touchstart\",i)},this.gf=()=>{t.removeEventListener(\"mousedown\",i)},t.addEventListener(\"mousedown\",i),t.addEventListener(\"touchstart\",i,{passive:!0})}ls()&&(this.xf=()=>{this.Zf.removeEventListener(\"dblclick\",this.Ef)},this.Zf.addEventListener(\"dblclick\",this.Ef)),this.Zf.addEventListener(\"mouseleave\",this.gv.bind(this)),this.Zf.addEventListener(\"touchstart\",this.fv.bind(this),{passive:!0}),bs(this.Zf),this.Zf.addEventListener(\"mousedown\",this.mv.bind(this)),this.Mv(),this.Zf.addEventListener(\"touchmove\",(()=>{}),{passive:!1})}Mv(){void 0===this.Hf.xv&&void 0===this.Hf.Sv&&void 0===this.Hf.kv||(this.Zf.addEventListener(\"touchstart\",(t=>this.yv(t.touches)),{passive:!0}),this.Zf.addEventListener(\"touchmove\",(t=>{if(2===t.touches.length&&null!==this.Cf&&void 0!==this.Hf.Sv){const i=gs(t.touches[0],t.touches[1])/this.Tf;this.Hf.Sv(this.Cf,i),Ms(t)}}),{passive:!1}),this.Zf.addEventListener(\"touchend\",(t=>{this.yv(t.touches)})))}yv(t){1===t.length&&(this.Pf=!1),2!==t.length||this.Pf||this.ff?this.Cv():this.Tv(t)}Tv(t){const i=this.Zf.getBoundingClientRect()||{left:0,top:0};this.Cf={nt:(t[0].clientX-i.left+(t[1].clientX-i.left))/2,st:(t[0].clientY-i.top+(t[1].clientY-i.top))/2},this.Tf=gs(t[0],t[1]),void 0!==this.Hf.xv&&this.Hf.xv(),this.Kf()}Cv(){null!==this.Cf&&(this.Cf=null,void 0!==this.Hf.kv&&this.Hf.kv())}gv(t){if(this.Sf&&this.Sf(),this.If(t))return;if(!this.Vf)return;const i=this.Lf(t);this.Uf(i,this.Hf.Pv),this.Vf=!ls()}vv(t){const i=ks(t.touches,f(this.Bf));if(null===i)return;const n=this.Lf(t,i);this.Wf(n,this.Hf.Rv),this.wf=!0,this.ff=!0}If(t){return t.sourceCapabilities&&void 0!==t.sourceCapabilities.firesTouchEvents?t.sourceCapabilities.firesTouchEvents:Ss(t)<this.Of+500}Wf(t,i){i&&i.call(this.Hf,t)}Uf(t,i){i&&i.call(this.Hf,t)}Lf(t,i){const n=i||t,s=this.Zf.getBoundingClientRect()||{left:0,top:0};return{clientX:n.clientX,clientY:n.clientY,pageX:n.pageX,pageY:n.pageY,screenX:n.screenX,screenY:n.screenY,localX:n.clientX-s.left,localY:n.clientY-s.top,ctrlKey:t.ctrlKey,altKey:t.altKey,shiftKey:t.shiftKey,metaKey:t.metaKey,Dv:!t.type.startsWith(\"mouse\")&&\"contextmenu\"!==t.type&&\"click\"!==t.type,Ov:t.type,Bv:n.target,Vv:t.view,Av:()=>{\"touchstart\"!==t.type&&Ms(t)}}}}function gs(t,i){const n=t.clientX-i.clientX,s=t.clientY-i.clientY;return Math.sqrt(n*n+s*s)}function Ms(t){t.cancelable&&t.preventDefault()}function xs(t){return{nt:t.pageX,st:t.pageY}}function Ss(t){return t.timeStamp||performance.now()}function ks(t,i){for(let n=0;n<t.length;++n)if(t[n].identifier===i)return t[n];return null}function ys(t){return{Hc:t.Hc,zv:{gr:t.Ev.externalId},Iv:t.Ev.cursorStyle}}function Cs(t,i,n){for(const s of t){const t=s.gt();if(null!==t&&t.wr){const e=t.wr(i,n);if(null!==e)return{Vv:s,zv:e}}}return null}function Ts(t,i){return n=>{var s,e,r,h;return(null!==(e=null===(s=n.Dt())||void 0===s?void 0:s.Pa())&&void 0!==e?e:\"\")!==i?[]:null!==(h=null===(r=n.da)||void 0===r?void 0:r.call(n,t))&&void 0!==h?h:[]}}function Ps(t,i,n,s){if(!t.length)return;let e=0;const r=n/2,h=t[0].At(s,!0);let l=1===i?r-(t[0].Oi()-h/2):t[0].Oi()-h/2-r;l=Math.max(0,l);for(let r=1;r<t.length;r++){const h=t[r],a=t[r-1],o=a.At(s,!1),_=h.Oi(),u=a.Oi();if(1===i?_>u-o:_<u+o){const s=u-o*i;h.Bi(s);const r=s-i*o/2;if((1===i?r<0:r>n)&&l>0){const s=1===i?-1-r:r-n,h=Math.min(s,l);for(let n=e;n<t.length;n++)t[n].Bi(t[n].Oi()+i*h);l-=h}}else e=r,l=1===i?u-o-_:_-(u+o)}}class Rs{constructor(t,i,n,s){this.Ii=null,this.Lv=null,this.Nv=!1,this.Fv=new Jt(200),this.Qr=null,this.Wv=0,this.jv=!1,this.Hv=()=>{this.jv||this.tn.$v().$t().Uh()},this.Uv=()=>{this.jv||this.tn.$v().$t().Uh()},this.tn=t,this.cn=i,this.ko=i.layout,this.Bc=n,this.qv=\"left\"===s,this.Yv=Ts(\"normal\",s),this.Zv=Ts(\"top\",s),this.Xv=Ts(\"bottom\",s),this.Kv=document.createElement(\"div\"),this.Kv.style.height=\"100%\",this.Kv.style.overflow=\"hidden\",this.Kv.style.width=\"25px\",this.Kv.style.left=\"0\",this.Kv.style.position=\"relative\",this.Gv=ds(this.Kv,Jn({width:16,height:16})),this.Gv.subscribeSuggestedBitmapSizeChanged(this.Hv);const e=this.Gv.canvasElement;e.style.position=\"absolute\",e.style.zIndex=\"1\",e.style.left=\"0\",e.style.top=\"0\",this.Jv=ds(this.Kv,Jn({width:16,height:16})),this.Jv.subscribeSuggestedBitmapSizeChanged(this.Uv);const r=this.Jv.canvasElement;r.style.position=\"absolute\",r.style.zIndex=\"2\",r.style.left=\"0\",r.style.top=\"0\";const h={bv:this.Qv.bind(this),pv:this.Qv.bind(this),av:this.tp.bind(this),hv:this.tp.bind(this),wv:this.ip.bind(this),cv:this.np.bind(this),_v:this.np.bind(this),qf:this.sp.bind(this),jf:this.sp.bind(this),Qf:this.ep.bind(this),Pv:this.rp.bind(this)};this.hp=new ws(this.Jv.canvasElement,h,{ev:()=>!this.cn.handleScroll.vertTouchDrag,rv:()=>!0})}S(){this.hp.S(),this.Jv.unsubscribeSuggestedBitmapSizeChanged(this.Uv),fs(this.Jv.canvasElement),this.Jv.dispose(),this.Gv.unsubscribeSuggestedBitmapSizeChanged(this.Hv),fs(this.Gv.canvasElement),this.Gv.dispose(),null!==this.Ii&&this.Ii.Ko().p(this),this.Ii=null}lp(){return this.Kv}P(){return this.ko.fontSize}ap(){const t=this.Bc.W();return this.Qr!==t.R&&(this.Fv.nr(),this.Qr=t.R),t}op(){if(null===this.Ii)return 0;let t=0;const i=this.ap(),n=f(this.Gv.canvasElement.getContext(\"2d\"));n.save();const s=this.Ii.Ha();n.font=this._p(),s.length>0&&(t=Math.max(this.Fv.xi(n,s[0].so),this.Fv.xi(n,s[s.length-1].so)));const e=this.up();for(let i=e.length;i--;){const s=this.Fv.xi(n,e[i].Kt());s>t&&(t=s)}const r=this.Ii.Ct();if(null!==r&&null!==this.Lv&&(2!==(h=this.cn.crosshair).mode&&h.horzLine.visible&&h.horzLine.labelVisible)){const i=this.Ii.pn(1,r),s=this.Ii.pn(this.Lv.height-2,r);t=Math.max(t,this.Fv.xi(n,this.Ii.Fi(Math.floor(Math.min(i,s))+.11111111111111,r)),this.Fv.xi(n,this.Ii.Fi(Math.ceil(Math.max(i,s))-.11111111111111,r)))}var h;n.restore();const l=t||34;return as(Math.ceil(i.C+i.T+i.A+i.I+5+l))}cp(t){null!==this.Lv&&Qn(this.Lv,t)||(this.Lv=t,this.jv=!0,this.Gv.resizeCanvasElement(t),this.Jv.resizeCanvasElement(t),this.jv=!1,this.Kv.style.width=`${t.width}px`,this.Kv.style.height=`${t.height}px`)}dp(){return f(this.Lv).width}Gi(t){this.Ii!==t&&(null!==this.Ii&&this.Ii.Ko().p(this),this.Ii=t,t.Ko().l(this.fo.bind(this),this))}Dt(){return this.Ii}nr(){const t=this.tn.fp();this.tn.$v().$t().L_(t,f(this.Dt()))}vp(t){if(null===this.Lv)return;if(1!==t){this.pp(),this.Gv.applySuggestedBitmapSize();const t=es(this.Gv);null!==t&&(t.useBitmapCoordinateSpace((t=>{this.mp(t),this.ze(t)})),this.tn.bp(t,this.Xv),this.wp(t),this.tn.bp(t,this.Yv),this.gp(t))}this.Jv.applySuggestedBitmapSize();const i=es(this.Jv);null!==i&&(i.useBitmapCoordinateSpace((({context:t,bitmapSize:i})=>{t.clearRect(0,0,i.width,i.height)})),this.Mp(i),this.tn.bp(i,this.Zv))}xp(){return this.Gv.bitmapSize}Sp(t,i,n){const s=this.xp();s.width>0&&s.height>0&&t.drawImage(this.Gv.canvasElement,i,n)}bt(){var t;null===(t=this.Ii)||void 0===t||t.Ha()}Qv(t){if(null===this.Ii||this.Ii.Ni()||!this.cn.handleScale.axisPressedMouseMove.price)return;const i=this.tn.$v().$t(),n=this.tn.fp();this.Nv=!0,i.O_(n,this.Ii,t.localY)}tp(t){if(null===this.Ii||!this.cn.handleScale.axisPressedMouseMove.price)return;const i=this.tn.$v().$t(),n=this.tn.fp(),s=this.Ii;i.B_(n,s,t.localY)}ip(){if(null===this.Ii||!this.cn.handleScale.axisPressedMouseMove.price)return;const t=this.tn.$v().$t(),i=this.tn.fp(),n=this.Ii;this.Nv&&(this.Nv=!1,t.V_(i,n))}np(t){if(null===this.Ii||!this.cn.handleScale.axisPressedMouseMove.price)return;const i=this.tn.$v().$t(),n=this.tn.fp();this.Nv=!1,i.V_(n,this.Ii)}sp(t){this.cn.handleScale.axisDoubleClickReset.price&&this.nr()}ep(t){if(null===this.Ii)return;!this.tn.$v().$t().W().handleScale.axisPressedMouseMove.price||this.Ii.Mh()||this.Ii.Bo()||this.kp(1)}rp(t){this.kp(0)}up(){const t=[],i=null===this.Ii?void 0:this.Ii;return(n=>{for(let s=0;s<n.length;++s){const e=n[s].Rn(this.tn.fp(),i);for(let i=0;i<e.length;i++)t.push(e[i])}})(this.tn.fp().Uo()),t}mp({context:t,bitmapSize:i}){const{width:n,height:s}=i,e=this.tn.fp().$t(),r=e.q(),h=e.bd();r===h?Y(t,0,0,n,s,r):K(t,0,0,n,s,r,h)}ze({context:t,bitmapSize:i,horizontalPixelRatio:n}){if(null===this.Lv||null===this.Ii||!this.Ii.W().borderVisible)return;t.fillStyle=this.Ii.W().borderColor;const s=Math.max(1,Math.floor(this.ap().C*n));let e;e=this.qv?i.width-s:0,t.fillRect(e,0,s,i.height)}wp(t){if(null===this.Lv||null===this.Ii)return;const i=this.Ii.Ha(),n=this.Ii.W(),s=this.ap(),e=this.qv?this.Lv.width-s.T:0;n.borderVisible&&n.ticksVisible&&t.useBitmapCoordinateSpace((({context:t,horizontalPixelRatio:r,verticalPixelRatio:h})=>{t.fillStyle=n.borderColor;const l=Math.max(1,Math.floor(h)),a=Math.floor(.5*h),o=Math.round(s.T*r);t.beginPath();for(const n of i)t.rect(Math.floor(e*r),Math.round(n.La*h)-a,o,l);t.fill()})),t.useMediaCoordinateSpace((({context:t})=>{var r;t.font=this._p(),t.fillStyle=null!==(r=n.textColor)&&void 0!==r?r:this.ko.textColor,t.textAlign=this.qv?\"right\":\"left\",t.textBaseline=\"middle\";const h=this.qv?Math.round(e-s.A):Math.round(e+s.T+s.A),l=i.map((i=>this.Fv.Mi(t,i.so)));for(let n=i.length;n--;){const s=i[n];t.fillText(s.so,h,s.La+l[n])}}))}pp(){if(null===this.Lv||null===this.Ii)return;const t=[],i=this.Ii.Uo().slice(),n=this.tn.fp(),s=this.ap();this.Ii===n.pr()&&this.tn.fp().Uo().forEach((t=>{n.vr(t)&&i.push(t)}));const e=this.Ii;i.forEach((i=>{i.Rn(n,e).forEach((i=>{i.Bi(null),i.Vi()&&t.push(i)}))})),t.forEach((t=>t.Bi(t.ki())));this.Ii.W().alignLabels&&this.yp(t,s)}yp(t,i){if(null===this.Lv)return;const n=this.Lv.height/2,s=t.filter((t=>t.ki()<=n)),e=t.filter((t=>t.ki()>n));s.sort(((t,i)=>i.ki()-t.ki())),e.sort(((t,i)=>t.ki()-i.ki()));for(const n of t){const t=Math.floor(n.At(i)/2),s=n.ki();s>-t&&s<t&&n.Bi(t),s>this.Lv.height-t&&s<this.Lv.height+t&&n.Bi(this.Lv.height-t)}Ps(s,1,this.Lv.height,i),Ps(e,-1,this.Lv.height,i)}gp(t){if(null===this.Lv)return;const i=this.up(),n=this.ap(),s=this.qv?\"right\":\"left\";i.forEach((i=>{if(i.Ai()){i.gt(f(this.Ii)).X(t,n,this.Fv,s)}}))}Mp(t){if(null===this.Lv||null===this.Ii)return;const i=this.tn.$v().$t(),n=[],s=this.tn.fp(),e=i.Zc().Rn(s,this.Ii);e.length&&n.push(e);const r=this.ap(),h=this.qv?\"right\":\"left\";n.forEach((i=>{i.forEach((i=>{i.gt(f(this.Ii)).X(t,r,this.Fv,h)}))}))}kp(t){this.Kv.style.cursor=1===t?\"ns-resize\":\"default\"}fo(){const t=this.op();this.Wv<t&&this.tn.$v().$t().Kl(),this.Wv=t}_p(){return E(this.ko.fontSize,this.ko.fontFamily)}}function Ds(t,i){var n,s;return null!==(s=null===(n=t.ua)||void 0===n?void 0:n.call(t,i))&&void 0!==s?s:[]}function Os(t,i){var n,s;return null!==(s=null===(n=t.Pn)||void 0===n?void 0:n.call(t,i))&&void 0!==s?s:[]}function Bs(t,i){var n,s;return null!==(s=null===(n=t.Ji)||void 0===n?void 0:n.call(t,i))&&void 0!==s?s:[]}function Vs(t,i){var n,s;return null!==(s=null===(n=t.aa)||void 0===n?void 0:n.call(t,i))&&void 0!==s?s:[]}class As{constructor(t,i){this.Lv=Jn({width:0,height:0}),this.Cp=null,this.Tp=null,this.Pp=null,this.Rp=null,this.Dp=!1,this.Op=new C,this.Bp=new C,this.Vp=0,this.Ap=!1,this.zp=null,this.Ep=!1,this.Ip=null,this.Lp=null,this.jv=!1,this.Hv=()=>{this.jv||null===this.Np||this.$i().Uh()},this.Uv=()=>{this.jv||null===this.Np||this.$i().Uh()},this.Qd=t,this.Np=i,this.Np.W_().l(this.Fp.bind(this),this,!0),this.Wp=document.createElement(\"td\"),this.Wp.style.padding=\"0\",this.Wp.style.position=\"relative\";const n=document.createElement(\"div\");n.style.width=\"100%\",n.style.height=\"100%\",n.style.position=\"relative\",n.style.overflow=\"hidden\",this.jp=document.createElement(\"td\"),this.jp.style.padding=\"0\",this.Hp=document.createElement(\"td\"),this.Hp.style.padding=\"0\",this.Wp.appendChild(n),this.Gv=ds(n,Jn({width:16,height:16})),this.Gv.subscribeSuggestedBitmapSizeChanged(this.Hv);const s=this.Gv.canvasElement;s.style.position=\"absolute\",s.style.zIndex=\"1\",s.style.left=\"0\",s.style.top=\"0\",this.Jv=ds(n,Jn({width:16,height:16})),this.Jv.subscribeSuggestedBitmapSizeChanged(this.Uv);const e=this.Jv.canvasElement;e.style.position=\"absolute\",e.style.zIndex=\"2\",e.style.left=\"0\",e.style.top=\"0\",this.$p=document.createElement(\"tr\"),this.$p.appendChild(this.jp),this.$p.appendChild(this.Wp),this.$p.appendChild(this.Hp),this.Up(),this.hp=new ws(this.Jv.canvasElement,this,{ev:()=>null===this.zp&&!this.Qd.W().handleScroll.vertTouchDrag,rv:()=>null===this.zp&&!this.Qd.W().handleScroll.horzTouchDrag})}S(){null!==this.Cp&&this.Cp.S(),null!==this.Tp&&this.Tp.S(),this.Pp=null,this.Jv.unsubscribeSuggestedBitmapSizeChanged(this.Uv),fs(this.Jv.canvasElement),this.Jv.dispose(),this.Gv.unsubscribeSuggestedBitmapSizeChanged(this.Hv),fs(this.Gv.canvasElement),this.Gv.dispose(),null!==this.Np&&this.Np.W_().p(this),this.hp.S()}fp(){return f(this.Np)}qp(t){var i,n;null!==this.Np&&this.Np.W_().p(this),this.Np=t,null!==this.Np&&this.Np.W_().l(As.prototype.Fp.bind(this),this,!0),this.Up(),this.Qd.Yp().indexOf(this)===this.Qd.Yp().length-1?(this.Pp=null!==(i=this.Pp)&&void 0!==i?i:new cs(this.Wp,this.Qd),this.Pp.bt()):(null===(n=this.Pp)||void 0===n||n.if(),this.Pp=null)}$v(){return this.Qd}lp(){return this.$p}Up(){if(null!==this.Np&&(this.Zp(),0!==this.$i().wt().length)){if(null!==this.Cp){const t=this.Np.R_();this.Cp.Gi(f(t))}if(null!==this.Tp){const t=this.Np.D_();this.Tp.Gi(f(t))}}}Xp(){null!==this.Cp&&this.Cp.bt(),null!==this.Tp&&this.Tp.bt()}M_(){return null!==this.Np?this.Np.M_():0}x_(t){this.Np&&this.Np.x_(t)}Qf(t){if(!this.Np)return;this.Kp();const i=t.localX,n=t.localY;this.Gp(i,n,t)}bv(t){this.Kp(),this.Jp(),this.Gp(t.localX,t.localY,t)}tv(t){var i;if(!this.Np)return;this.Kp();const n=t.localX,s=t.localY;this.Gp(n,s,t);const e=this.wr(n,s);this.Qd.Qp(null!==(i=null==e?void 0:e.Iv)&&void 0!==i?i:null),this.$i().jc(e&&{Hc:e.Hc,zv:e.zv})}dv(t){null!==this.Np&&(this.Kp(),this.tm(t))}qf(t){null!==this.Np&&this.im(this.Bp,t)}jf(t){this.qf(t)}av(t){this.Kp(),this.nm(t),this.Gp(t.localX,t.localY,t)}cv(t){null!==this.Np&&(this.Kp(),this.Ap=!1,this.sm(t))}uv(t){null!==this.Np&&this.tm(t)}Rv(t){if(this.Ap=!0,null===this.zp){const i={x:t.localX,y:t.localY};this.rm(i,i,t)}}Pv(t){null!==this.Np&&(this.Kp(),this.Np.$t().jc(null),this.hm())}lm(){return this.Op}am(){return this.Bp}xv(){this.Vp=1,this.$i().Un()}Sv(t,i){if(!this.Qd.W().handleScale.pinch)return;const n=5*(i-this.Vp);this.Vp=i,this.$i().Qc(t.nt,n)}pv(t){this.Ap=!1,this.Ep=null!==this.zp,this.Jp();const i=this.$i().Zc();null!==this.zp&&i.yt()&&(this.Ip={x:i.Yt(),y:i.Zt()},this.zp={x:t.localX,y:t.localY})}hv(t){if(null===this.Np)return;const i=t.localX,n=t.localY;if(null===this.zp)this.nm(t);else{this.Ep=!1;const s=f(this.Ip),e=s.x+(i-this.zp.x),r=s.y+(n-this.zp.y);this.Gp(e,r,t)}}_v(t){0===this.$v().W().trackingMode.exitMode&&(this.Ep=!0),this.om(),this.sm(t)}wr(t,i){const n=this.Np;return null===n?null:function(t,i,n){const s=t.Uo(),e=function(t,i,n){var s,e;let r,h;for(const o of t){const t=null!==(e=null===(s=o.va)||void 0===s?void 0:s.call(o,i,n))&&void 0!==e?e:[];for(const i of t)l=i.zOrder,(!(a=null==r?void 0:r.zOrder)||\"top\"===l&&\"top\"!==a||\"normal\"===l&&\"bottom\"===a)&&(r=i,h=o)}var l,a;return r&&h?{Ev:r,Hc:h}:null}(s,i,n);if(\"top\"===(null==e?void 0:e.Ev.zOrder))return ys(e);for(const r of s){if(e&&e.Hc===r&&\"bottom\"!==e.Ev.zOrder&&!e.Ev.isBackground)return ys(e);const s=Cs(r.Pn(t),i,n);if(null!==s)return{Hc:r,Vv:s.Vv,zv:s.zv};if(e&&e.Hc===r&&\"bottom\"!==e.Ev.zOrder&&e.Ev.isBackground)return ys(e)}return(null==e?void 0:e.Ev)?ys(e):null}(n,t,i)}_m(t,i){f(\"left\"===i?this.Cp:this.Tp).cp(Jn({width:t,height:this.Lv.height}))}um(){return this.Lv}cp(t){Qn(this.Lv,t)||(this.Lv=t,this.jv=!0,this.Gv.resizeCanvasElement(t),this.Jv.resizeCanvasElement(t),this.jv=!1,this.Wp.style.width=t.width+\"px\",this.Wp.style.height=t.height+\"px\")}dm(){const t=f(this.Np);t.P_(t.R_()),t.P_(t.D_());for(const i of t.Va())if(t.vr(i)){const n=i.Dt();null!==n&&t.P_(n),i.On()}}xp(){return this.Gv.bitmapSize}Sp(t,i,n){const s=this.xp();s.width>0&&s.height>0&&t.drawImage(this.Gv.canvasElement,i,n)}vp(t){if(0===t)return;if(null===this.Np)return;if(t>1&&this.dm(),null!==this.Cp&&this.Cp.vp(t),null!==this.Tp&&this.Tp.vp(t),1!==t){this.Gv.applySuggestedBitmapSize();const t=es(this.Gv);null!==t&&(t.useBitmapCoordinateSpace((t=>{this.mp(t)})),this.Np&&(this.fm(t,Ds),this.vm(t),this.pm(t),this.fm(t,Os),this.fm(t,Bs)))}this.Jv.applySuggestedBitmapSize();const i=es(this.Jv);null!==i&&(i.useBitmapCoordinateSpace((({context:t,bitmapSize:i})=>{t.clearRect(0,0,i.width,i.height)})),this.bm(i),this.fm(i,Vs))}wm(){return this.Cp}gm(){return this.Tp}bp(t,i){this.fm(t,i)}Fp(){null!==this.Np&&this.Np.W_().p(this),this.Np=null}tm(t){this.im(this.Op,t)}im(t,i){const n=i.localX,s=i.localY;t.M()&&t.m(this.$i().St().Nu(n),{x:n,y:s},i)}mp({context:t,bitmapSize:i}){const{width:n,height:s}=i,e=this.$i(),r=e.q(),h=e.bd();r===h?Y(t,0,0,n,s,h):K(t,0,0,n,s,r,h)}vm(t){const i=f(this.Np).j_().qh().gt();null!==i&&i.X(t,!1)}pm(t){const i=this.$i().Yc();this.Mm(t,Os,vs,i),this.Mm(t,Os,ps,i)}bm(t){this.Mm(t,Os,ps,this.$i().Zc())}fm(t,i){const n=f(this.Np).Uo();for(const s of n)this.Mm(t,i,vs,s);for(const s of n)this.Mm(t,i,ps,s)}Mm(t,i,n,s){const e=f(this.Np),r=e.$t().Wc(),h=null!==r&&r.Hc===s,l=null!==r&&h&&void 0!==r.zv?r.zv.Mr:void 0;ms(i,(i=>n(i,t,h,l)),s,e)}Zp(){if(null===this.Np)return;const t=this.Qd,i=this.Np.R_().W().visible,n=this.Np.D_().W().visible;i||null===this.Cp||(this.jp.removeChild(this.Cp.lp()),this.Cp.S(),this.Cp=null),n||null===this.Tp||(this.Hp.removeChild(this.Tp.lp()),this.Tp.S(),this.Tp=null);const s=t.$t().ud();i&&null===this.Cp&&(this.Cp=new Rs(this,t.W(),s,\"left\"),this.jp.appendChild(this.Cp.lp())),n&&null===this.Tp&&(this.Tp=new Rs(this,t.W(),s,\"right\"),this.Hp.appendChild(this.Tp.lp()))}xm(t){return t.Dv&&this.Ap||null!==this.zp}Sm(t){return Math.max(0,Math.min(t,this.Lv.width-1))}km(t){return Math.max(0,Math.min(t,this.Lv.height-1))}Gp(t,i,n){this.$i().ld(this.Sm(t),this.km(i),n,f(this.Np))}hm(){this.$i().od()}om(){this.Ep&&(this.zp=null,this.hm())}rm(t,i,n){this.zp=t,this.Ep=!1,this.Gp(i.x,i.y,n);const s=this.$i().Zc();this.Ip={x:s.Yt(),y:s.Zt()}}$i(){return this.Qd.$t()}sm(t){if(!this.Dp)return;const i=this.$i(),n=this.fp();if(i.E_(n,n.vn()),this.Rp=null,this.Dp=!1,i.ed(),null!==this.Lp){const t=performance.now(),n=i.St();this.Lp.Or(n.Hu(),t),this.Lp.Qu(t)||i.Zn(this.Lp)}}Kp(){this.zp=null}Jp(){if(!this.Np)return;if(this.$i().Un(),document.activeElement!==document.body&&document.activeElement!==document.documentElement)f(document.activeElement).blur();else{const t=document.getSelection();null!==t&&t.removeAllRanges()}!this.Np.vn().Ni()&&this.$i().St().Ni()}nm(t){if(null===this.Np)return;const i=this.$i(),n=i.St();if(n.Ni())return;const s=this.Qd.W(),e=s.handleScroll,r=s.kineticScroll;if((!e.pressedMouseMove||t.Dv)&&(!e.horzTouchDrag&&!e.vertTouchDrag||!t.Dv))return;const h=this.Np.vn(),l=performance.now();if(null!==this.Rp||this.xm(t)||(this.Rp={x:t.clientX,y:t.clientY,Bd:l,ym:t.localX,Cm:t.localY}),null!==this.Rp&&!this.Dp&&(this.Rp.x!==t.clientX||this.Rp.y!==t.clientY)){if(t.Dv&&r.touch||!t.Dv&&r.mouse){const t=n.le();this.Lp=new us(.2/t,7/t,.997,15/t),this.Lp.Yd(n.Hu(),this.Rp.Bd)}else this.Lp=null;h.Ni()||i.A_(this.Np,h,t.localY),i.nd(t.localX),this.Dp=!0}this.Dp&&(h.Ni()||i.z_(this.Np,h,t.localY),i.sd(t.localX),null!==this.Lp&&this.Lp.Yd(n.Hu(),l))}}class zs{constructor(t,i,n,s,e){this.ft=!0,this.Lv=Jn({width:0,height:0}),this.Hv=()=>this.vp(3),this.qv=\"left\"===t,this.Bc=n.ud,this.cn=i,this.Tm=s,this.Pm=e,this.Kv=document.createElement(\"div\"),this.Kv.style.width=\"25px\",this.Kv.style.height=\"100%\",this.Kv.style.overflow=\"hidden\",this.Gv=ds(this.Kv,Jn({width:16,height:16})),this.Gv.subscribeSuggestedBitmapSizeChanged(this.Hv)}S(){this.Gv.unsubscribeSuggestedBitmapSizeChanged(this.Hv),fs(this.Gv.canvasElement),this.Gv.dispose()}lp(){return this.Kv}um(){return this.Lv}cp(t){Qn(this.Lv,t)||(this.Lv=t,this.Gv.resizeCanvasElement(t),this.Kv.style.width=`${t.width}px`,this.Kv.style.height=`${t.height}px`,this.ft=!0)}vp(t){if(t<3&&!this.ft)return;if(0===this.Lv.width||0===this.Lv.height)return;this.ft=!1,this.Gv.applySuggestedBitmapSize();const i=es(this.Gv);null!==i&&i.useBitmapCoordinateSpace((t=>{this.mp(t),this.ze(t)}))}xp(){return this.Gv.bitmapSize}Sp(t,i,n){const s=this.xp();s.width>0&&s.height>0&&t.drawImage(this.Gv.canvasElement,i,n)}ze({context:t,bitmapSize:i,horizontalPixelRatio:n,verticalPixelRatio:s}){if(!this.Tm())return;t.fillStyle=this.cn.timeScale.borderColor;const e=Math.floor(this.Bc.W().C*n),r=Math.floor(this.Bc.W().C*s),h=this.qv?i.width-e:0;t.fillRect(h,0,e,r)}mp({context:t,bitmapSize:i}){Y(t,0,0,i.width,i.height,this.Pm())}}function Es(t){return i=>{var n,s;return null!==(s=null===(n=i.fa)||void 0===n?void 0:n.call(i,t))&&void 0!==s?s:[]}}const Is=Es(\"normal\"),Ls=Es(\"top\"),Ns=Es(\"bottom\");class Fs{constructor(t,i){this.Rm=null,this.Dm=null,this.k=null,this.Om=!1,this.Lv=Jn({width:0,height:0}),this.Bm=new C,this.Fv=new Jt(5),this.jv=!1,this.Hv=()=>{this.jv||this.Qd.$t().Uh()},this.Uv=()=>{this.jv||this.Qd.$t().Uh()},this.Qd=t,this.q_=i,this.cn=t.W().layout,this.Xd=document.createElement(\"tr\"),this.Vm=document.createElement(\"td\"),this.Vm.style.padding=\"0\",this.Am=document.createElement(\"td\"),this.Am.style.padding=\"0\",this.Kv=document.createElement(\"td\"),this.Kv.style.height=\"25px\",this.Kv.style.padding=\"0\",this.zm=document.createElement(\"div\"),this.zm.style.width=\"100%\",this.zm.style.height=\"100%\",this.zm.style.position=\"relative\",this.zm.style.overflow=\"hidden\",this.Kv.appendChild(this.zm),this.Gv=ds(this.zm,Jn({width:16,height:16})),this.Gv.subscribeSuggestedBitmapSizeChanged(this.Hv);const n=this.Gv.canvasElement;n.style.position=\"absolute\",n.style.zIndex=\"1\",n.style.left=\"0\",n.style.top=\"0\",this.Jv=ds(this.zm,Jn({width:16,height:16})),this.Jv.subscribeSuggestedBitmapSizeChanged(this.Uv);const s=this.Jv.canvasElement;s.style.position=\"absolute\",s.style.zIndex=\"2\",s.style.left=\"0\",s.style.top=\"0\",this.Xd.appendChild(this.Vm),this.Xd.appendChild(this.Kv),this.Xd.appendChild(this.Am),this.Em(),this.Qd.$t().g_().l(this.Em.bind(this),this),this.hp=new ws(this.Jv.canvasElement,this,{ev:()=>!0,rv:()=>!this.Qd.W().handleScroll.horzTouchDrag})}S(){this.hp.S(),null!==this.Rm&&this.Rm.S(),null!==this.Dm&&this.Dm.S(),this.Jv.unsubscribeSuggestedBitmapSizeChanged(this.Uv),fs(this.Jv.canvasElement),this.Jv.dispose(),this.Gv.unsubscribeSuggestedBitmapSizeChanged(this.Hv),fs(this.Gv.canvasElement),this.Gv.dispose()}lp(){return this.Xd}Im(){return this.Rm}Lm(){return this.Dm}bv(t){if(this.Om)return;this.Om=!0;const i=this.Qd.$t();!i.St().Ni()&&this.Qd.W().handleScale.axisPressedMouseMove.time&&i.Jc(t.localX)}pv(t){this.bv(t)}wv(){const t=this.Qd.$t();!t.St().Ni()&&this.Om&&(this.Om=!1,this.Qd.W().handleScale.axisPressedMouseMove.time&&t.hd())}av(t){const i=this.Qd.$t();!i.St().Ni()&&this.Qd.W().handleScale.axisPressedMouseMove.time&&i.rd(t.localX)}hv(t){this.av(t)}cv(){this.Om=!1;const t=this.Qd.$t();t.St().Ni()&&!this.Qd.W().handleScale.axisPressedMouseMove.time||t.hd()}_v(){this.cv()}qf(){this.Qd.W().handleScale.axisDoubleClickReset.time&&this.Qd.$t().Kn()}jf(){this.qf()}Qf(){this.Qd.$t().W().handleScale.axisPressedMouseMove.time&&this.kp(1)}Pv(){this.kp(0)}um(){return this.Lv}Nm(){return this.Bm}Fm(t,i,n){Qn(this.Lv,t)||(this.Lv=t,this.jv=!0,this.Gv.resizeCanvasElement(t),this.Jv.resizeCanvasElement(t),this.jv=!1,this.Kv.style.width=`${t.width}px`,this.Kv.style.height=`${t.height}px`,this.Bm.m(t)),null!==this.Rm&&this.Rm.cp(Jn({width:i,height:t.height})),null!==this.Dm&&this.Dm.cp(Jn({width:n,height:t.height}))}Wm(){const t=this.jm();return Math.ceil(t.C+t.T+t.P+t.L+t.V+t.Hm)}bt(){this.Qd.$t().St().Ha()}xp(){return this.Gv.bitmapSize}Sp(t,i,n){const s=this.xp();s.width>0&&s.height>0&&t.drawImage(this.Gv.canvasElement,i,n)}vp(t){if(0===t)return;if(1!==t){this.Gv.applySuggestedBitmapSize();const i=es(this.Gv);null!==i&&(i.useBitmapCoordinateSpace((t=>{this.mp(t),this.ze(t),this.$m(i,Ns)})),this.wp(i),this.$m(i,Is)),null!==this.Rm&&this.Rm.vp(t),null!==this.Dm&&this.Dm.vp(t)}this.Jv.applySuggestedBitmapSize();const i=es(this.Jv);null!==i&&(i.useBitmapCoordinateSpace((({context:t,bitmapSize:i})=>{t.clearRect(0,0,i.width,i.height)})),this.Um([...this.Qd.$t().wt(),this.Qd.$t().Zc()],i),this.$m(i,Ls))}$m(t,i){const n=this.Qd.$t().wt();for(const s of n)ms(i,(i=>vs(i,t,!1,void 0)),s,void 0);for(const s of n)ms(i,(i=>ps(i,t,!1,void 0)),s,void 0)}mp({context:t,bitmapSize:i}){Y(t,0,0,i.width,i.height,this.Qd.$t().bd())}ze({context:t,bitmapSize:i,verticalPixelRatio:n}){if(this.Qd.W().timeScale.borderVisible){t.fillStyle=this.qm();const s=Math.max(1,Math.floor(this.jm().C*n));t.fillRect(0,0,i.width,s)}}wp(t){const i=this.Qd.$t().St(),n=i.Ha();if(!n||0===n.length)return;const s=this.q_.maxTickMarkWeight(n),e=this.jm(),r=i.W();r.borderVisible&&r.ticksVisible&&t.useBitmapCoordinateSpace((({context:t,horizontalPixelRatio:i,verticalPixelRatio:s})=>{t.strokeStyle=this.qm(),t.fillStyle=this.qm();const r=Math.max(1,Math.floor(i)),h=Math.floor(.5*i);t.beginPath();const l=Math.round(e.T*s);for(let s=n.length;s--;){const e=Math.round(n[s].coord*i);t.rect(e-h,0,r,l)}t.fill()})),t.useMediaCoordinateSpace((({context:t})=>{const i=e.C+e.T+e.L+e.P/2;t.textAlign=\"center\",t.textBaseline=\"middle\",t.fillStyle=this.$(),t.font=this._p();for(const e of n)if(e.weight<s){const n=e.needAlignCoordinate?this.Ym(t,e.coord,e.label):e.coord;t.fillText(e.label,n,i)}this.Qd.W().timeScale.allowBoldLabels&&(t.font=this.Zm());for(const e of n)if(e.weight>=s){const n=e.needAlignCoordinate?this.Ym(t,e.coord,e.label):e.coord;t.fillText(e.label,n,i)}}))}Ym(t,i,n){const s=this.Fv.xi(t,n),e=s/2,r=Math.floor(i-e)+.5;return r<0?i+=Math.abs(0-r):r+s>this.Lv.width&&(i-=Math.abs(this.Lv.width-(r+s))),i}Um(t,i){const n=this.jm();for(const s of t)for(const t of s.Qi())t.gt().X(i,n)}qm(){return this.Qd.W().timeScale.borderColor}$(){return this.cn.textColor}j(){return this.cn.fontSize}_p(){return E(this.j(),this.cn.fontFamily)}Zm(){return E(this.j(),this.cn.fontFamily,\"bold\")}jm(){null===this.k&&(this.k={C:1,N:NaN,L:NaN,V:NaN,ji:NaN,T:5,P:NaN,R:\"\",Wi:new Jt,Hm:0});const t=this.k,i=this._p();if(t.R!==i){const n=this.j();t.P=n,t.R=i,t.L=3*n/12,t.V=3*n/12,t.ji=9*n/12,t.N=0,t.Hm=4*n/12,t.Wi.nr()}return this.k}kp(t){this.Kv.style.cursor=1===t?\"ew-resize\":\"default\"}Em(){const t=this.Qd.$t(),i=t.W();i.leftPriceScale.visible||null===this.Rm||(this.Vm.removeChild(this.Rm.lp()),this.Rm.S(),this.Rm=null),i.rightPriceScale.visible||null===this.Dm||(this.Am.removeChild(this.Dm.lp()),this.Dm.S(),this.Dm=null);const n={ud:this.Qd.$t().ud()},s=()=>i.leftPriceScale.borderVisible&&t.St().W().borderVisible,e=()=>t.bd();i.leftPriceScale.visible&&null===this.Rm&&(this.Rm=new zs(\"left\",i,n,s,e),this.Vm.appendChild(this.Rm.lp())),i.rightPriceScale.visible&&null===this.Dm&&(this.Dm=new zs(\"right\",i,n,s,e),this.Am.appendChild(this.Dm.lp()))}}const Ws=!!rs&&!!navigator.userAgentData&&navigator.userAgentData.brands.some((t=>t.brand.includes(\"Chromium\")))&&!!rs&&((null===(js=null===navigator||void 0===navigator?void 0:navigator.userAgentData)||void 0===js?void 0:js.platform)?\"Windows\"===navigator.userAgentData.platform:navigator.userAgent.toLowerCase().indexOf(\"win\")>=0);var js;class Hs{constructor(t,i,n){var s;this.Xm=[],this.Km=0,this.ho=0,this.__=0,this.Gm=0,this.Jm=0,this.Qm=null,this.tb=!1,this.Op=new C,this.Bp=new C,this.Rc=new C,this.ib=null,this.nb=null,this.Jd=t,this.cn=i,this.q_=n,this.Xd=document.createElement(\"div\"),this.Xd.classList.add(\"tv-lightweight-charts\"),this.Xd.style.overflow=\"hidden\",this.Xd.style.direction=\"ltr\",this.Xd.style.width=\"100%\",this.Xd.style.height=\"100%\",(s=this.Xd).style.userSelect=\"none\",s.style.webkitUserSelect=\"none\",s.style.msUserSelect=\"none\",s.style.MozUserSelect=\"none\",s.style.webkitTapHighlightColor=\"transparent\",this.sb=document.createElement(\"table\"),this.sb.setAttribute(\"cellspacing\",\"0\"),this.Xd.appendChild(this.sb),this.eb=this.rb.bind(this),$s(this.cn)&&this.hb(!0),this.$i=new Vn(this.Oc.bind(this),this.cn,n),this.$t().Xc().l(this.lb.bind(this),this),this.ab=new Fs(this,this.q_),this.sb.appendChild(this.ab.lp());const e=i.autoSize&&this.ob();let r=this.cn.width,h=this.cn.height;if(e||0===r||0===h){const i=t.getBoundingClientRect();r=r||i.width,h=h||i.height}this._b(r,h),this.ub(),t.appendChild(this.Xd),this.cb(),this.$i.St().ec().l(this.$i.Kl.bind(this.$i),this),this.$i.g_().l(this.$i.Kl.bind(this.$i),this)}$t(){return this.$i}W(){return this.cn}Yp(){return this.Xm}fb(){return this.ab}S(){this.hb(!1),0!==this.Km&&window.cancelAnimationFrame(this.Km),this.$i.Xc().p(this),this.$i.St().ec().p(this),this.$i.g_().p(this),this.$i.S();for(const t of this.Xm)this.sb.removeChild(t.lp()),t.lm().p(this),t.am().p(this),t.S();this.Xm=[],f(this.ab).S(),null!==this.Xd.parentElement&&this.Xd.parentElement.removeChild(this.Xd),this.Rc.S(),this.Op.S(),this.Bp.S(),this.pb()}_b(t,i,n=!1){if(this.ho===i&&this.__===t)return;const s=function(t){const i=Math.floor(t.width),n=Math.floor(t.height);return Jn({width:i-i%2,height:n-n%2})}(Jn({width:t,height:i}));this.ho=s.height,this.__=s.width;const e=this.ho+\"px\",r=this.__+\"px\";f(this.Xd).style.height=e,f(this.Xd).style.width=r,this.sb.style.height=e,this.sb.style.width=r,n?this.mb(lt.es(),performance.now()):this.$i.Kl()}vp(t){void 0===t&&(t=lt.es());for(let i=0;i<this.Xm.length;i++)this.Xm[i].vp(t.Hn(i).Fn);this.cn.timeScale.visible&&this.ab.vp(t.jn())}$h(t){const i=$s(this.cn);this.$i.$h(t);const n=$s(this.cn);n!==i&&this.hb(n),this.cb(),this.bb(t)}lm(){return this.Op}am(){return this.Bp}Xc(){return this.Rc}wb(){null!==this.Qm&&(this.mb(this.Qm,performance.now()),this.Qm=null);const t=this.gb(null),i=document.createElement(\"canvas\");i.width=t.width,i.height=t.height;const n=f(i.getContext(\"2d\"));return this.gb(n),i}Mb(t){if(\"left\"===t&&!this.xb())return 0;if(\"right\"===t&&!this.Sb())return 0;if(0===this.Xm.length)return 0;return f(\"left\"===t?this.Xm[0].wm():this.Xm[0].gm()).dp()}kb(){return this.cn.autoSize&&null!==this.ib}yb(){return this.Xd}Qp(t){this.nb=t,this.nb?this.yb().style.setProperty(\"cursor\",t):this.yb().style.removeProperty(\"cursor\")}Cb(){return this.nb}Tb(){return d(this.Xm[0]).um()}bb(t){(void 0!==t.autoSize||!this.ib||void 0===t.width&&void 0===t.height)&&(t.autoSize&&!this.ib&&this.ob(),!1===t.autoSize&&null!==this.ib&&this.pb(),t.autoSize||void 0===t.width&&void 0===t.height||this._b(t.width||this.__,t.height||this.ho))}gb(t){let i=0,n=0;const s=this.Xm[0],e=(i,n)=>{let s=0;for(let e=0;e<this.Xm.length;e++){const r=this.Xm[e],h=f(\"left\"===i?r.wm():r.gm()),l=h.xp();null!==t&&h.Sp(t,n,s),s+=l.height}};if(this.xb()){e(\"left\",0);i+=f(s.wm()).xp().width}for(let s=0;s<this.Xm.length;s++){const e=this.Xm[s],r=e.xp();null!==t&&e.Sp(t,i,n),n+=r.height}if(i+=s.xp().width,this.Sb()){e(\"right\",i);i+=f(s.gm()).xp().width}const r=(i,n,s)=>{f(\"left\"===i?this.ab.Im():this.ab.Lm()).Sp(f(t),n,s)};if(this.cn.timeScale.visible){const i=this.ab.xp();if(null!==t){let e=0;this.xb()&&(r(\"left\",e,n),e=f(s.wm()).xp().width),this.ab.Sp(t,e,n),e+=i.width,this.Sb()&&r(\"right\",e,n)}n+=i.height}return Jn({width:i,height:n})}Pb(){let t=0,i=0,n=0;for(const s of this.Xm)this.xb()&&(i=Math.max(i,f(s.wm()).op(),this.cn.leftPriceScale.minimumWidth)),this.Sb()&&(n=Math.max(n,f(s.gm()).op(),this.cn.rightPriceScale.minimumWidth)),t+=s.M_();i=as(i),n=as(n);const s=this.__,e=this.ho,r=Math.max(s-i-n,0),h=this.cn.timeScale.visible;let l=h?Math.max(this.ab.Wm(),this.cn.timeScale.minimumHeight):0;var a;l=(a=l)+a%2;const o=0+l,_=e<o?0:e-o,u=_/t;let c=0;for(let t=0;t<this.Xm.length;++t){const s=this.Xm[t];s.qp(this.$i.qc()[t]);let e=0,h=0;h=t===this.Xm.length-1?_-c:Math.round(s.M_()*u),e=Math.max(h,2),c+=e,s.cp(Jn({width:r,height:e})),this.xb()&&s._m(i,\"left\"),this.Sb()&&s._m(n,\"right\"),s.fp()&&this.$i.Kc(s.fp(),e)}this.ab.Fm(Jn({width:h?r:0,height:l}),h?i:0,h?n:0),this.$i.S_(r),this.Gm!==i&&(this.Gm=i),this.Jm!==n&&(this.Jm=n)}hb(t){t?this.Xd.addEventListener(\"wheel\",this.eb,{passive:!1}):this.Xd.removeEventListener(\"wheel\",this.eb)}Rb(t){switch(t.deltaMode){case t.DOM_DELTA_PAGE:return 120;case t.DOM_DELTA_LINE:return 32}return Ws?1/window.devicePixelRatio:1}rb(t){if(!(0!==t.deltaX&&this.cn.handleScroll.mouseWheel||0!==t.deltaY&&this.cn.handleScale.mouseWheel))return;const i=this.Rb(t),n=i*t.deltaX/100,s=-i*t.deltaY/100;if(t.cancelable&&t.preventDefault(),0!==s&&this.cn.handleScale.mouseWheel){const i=Math.sign(s)*Math.min(1,Math.abs(s)),n=t.clientX-this.Xd.getBoundingClientRect().left;this.$t().Qc(n,i)}0!==n&&this.cn.handleScroll.mouseWheel&&this.$t().td(-80*n)}mb(t,i){var n;const s=t.jn();3===s&&this.Db(),3!==s&&2!==s||(this.Ob(t),this.Bb(t,i),this.ab.bt(),this.Xm.forEach((t=>{t.Xp()})),3===(null===(n=this.Qm)||void 0===n?void 0:n.jn())&&(this.Qm.ts(t),this.Db(),this.Ob(this.Qm),this.Bb(this.Qm,i),t=this.Qm,this.Qm=null)),this.vp(t)}Bb(t,i){for(const n of t.Qn())this.ns(n,i)}Ob(t){const i=this.$i.qc();for(let n=0;n<i.length;n++)t.Hn(n).Wn&&i[n].N_()}ns(t,i){const n=this.$i.St();switch(t.qn){case 0:n.hc();break;case 1:n.lc(t.Ot);break;case 2:n.Gn(t.Ot);break;case 3:n.Jn(t.Ot);break;case 4:n.qu();break;case 5:t.Ot.Qu(i)||n.Jn(t.Ot.tc(i))}}Oc(t){null!==this.Qm?this.Qm.ts(t):this.Qm=t,this.tb||(this.tb=!0,this.Km=window.requestAnimationFrame((t=>{if(this.tb=!1,this.Km=0,null!==this.Qm){const i=this.Qm;this.Qm=null,this.mb(i,t);for(const n of i.Qn())if(5===n.qn&&!n.Ot.Qu(t)){this.$t().Zn(n.Ot);break}}})))}Db(){this.ub()}ub(){const t=this.$i.qc(),i=t.length,n=this.Xm.length;for(let t=i;t<n;t++){const t=d(this.Xm.pop());this.sb.removeChild(t.lp()),t.lm().p(this),t.am().p(this),t.S()}for(let s=n;s<i;s++){const i=new As(this,t[s]);i.lm().l(this.Vb.bind(this),this),i.am().l(this.Ab.bind(this),this),this.Xm.push(i),this.sb.insertBefore(i.lp(),this.ab.lp())}for(let n=0;n<i;n++){const i=t[n],s=this.Xm[n];s.fp()!==i?s.qp(i):s.Up()}this.cb(),this.Pb()}zb(t,i,n){var s;const e=new Map;if(null!==t){this.$i.wt().forEach((i=>{const n=i.zn().ll(t);null!==n&&e.set(i,n)}))}let r;if(null!==t){const i=null===(s=this.$i.St().Ui(t))||void 0===s?void 0:s.originalTime;void 0!==i&&(r=i)}const h=this.$t().Wc(),l=null!==h&&h.Hc instanceof Yi?h.Hc:void 0,a=null!==h&&void 0!==h.zv?h.zv.gr:void 0;return{Eb:r,ee:null!=t?t:void 0,Ib:null!=i?i:void 0,Lb:l,Nb:e,Fb:a,Wb:null!=n?n:void 0}}Vb(t,i,n){this.Op.m((()=>this.zb(t,i,n)))}Ab(t,i,n){this.Bp.m((()=>this.zb(t,i,n)))}lb(t,i,n){this.Rc.m((()=>this.zb(t,i,n)))}cb(){const t=this.cn.timeScale.visible?\"\":\"none\";this.ab.lp().style.display=t}xb(){return this.Xm[0].fp().R_().W().visible}Sb(){return this.Xm[0].fp().D_().W().visible}ob(){return\"ResizeObserver\"in window&&(this.ib=new ResizeObserver((t=>{const i=t.find((t=>t.target===this.Jd));i&&this._b(i.contentRect.width,i.contentRect.height)})),this.ib.observe(this.Jd,{box:\"border-box\"}),!0)}pb(){null!==this.ib&&this.ib.disconnect(),this.ib=null}}function $s(t){return Boolean(t.handleScroll.mouseWheel||t.handleScale.mouseWheel)}function Us(t){return function(t){return void 0!==t.open}(t)||function(t){return void 0!==t.value}(t)}function qs(t,i){var n={};for(var s in t)Object.prototype.hasOwnProperty.call(t,s)&&i.indexOf(s)<0&&(n[s]=t[s]);if(null!=t&&\"function\"==typeof Object.getOwnPropertySymbols){var e=0;for(s=Object.getOwnPropertySymbols(t);e<s.length;e++)i.indexOf(s[e])<0&&Object.prototype.propertyIsEnumerable.call(t,s[e])&&(n[s[e]]=t[s[e]])}return n}function Ys(t,i,n,s){const e=n.value,r={ee:i,ot:t,Ot:[e,e,e,e],Eb:s};return void 0!==n.color&&(r.O=n.color),r}function Zs(t,i,n,s){const e=n.value,r={ee:i,ot:t,Ot:[e,e,e,e],Eb:s};return void 0!==n.lineColor&&(r.lt=n.lineColor),void 0!==n.topColor&&(r.Ps=n.topColor),void 0!==n.bottomColor&&(r.Rs=n.bottomColor),r}function Xs(t,i,n,s){const e=n.value,r={ee:i,ot:t,Ot:[e,e,e,e],Eb:s};return void 0!==n.topLineColor&&(r.Re=n.topLineColor),void 0!==n.bottomLineColor&&(r.De=n.bottomLineColor),void 0!==n.topFillColor1&&(r.ke=n.topFillColor1),void 0!==n.topFillColor2&&(r.ye=n.topFillColor2),void 0!==n.bottomFillColor1&&(r.Ce=n.bottomFillColor1),void 0!==n.bottomFillColor2&&(r.Te=n.bottomFillColor2),r}function Ks(t,i,n,s){const e={ee:i,ot:t,Ot:[n.open,n.high,n.low,n.close],Eb:s};return void 0!==n.color&&(e.O=n.color),e}function Gs(t,i,n,s){const e={ee:i,ot:t,Ot:[n.open,n.high,n.low,n.close],Eb:s};return void 0!==n.color&&(e.O=n.color),void 0!==n.borderColor&&(e.Bt=n.borderColor),void 0!==n.wickColor&&(e.Xh=n.wickColor),e}function Js(t,i,n,s,e){const r=d(e)(n),h=Math.max(...r),l=Math.min(...r),a=r[r.length-1],o=[a,h,l,a],_=n,{time:u,color:c}=_;return{ee:i,ot:t,Ot:o,Eb:s,$e:qs(_,[\"time\",\"color\"]),O:c}}function Qs(t){return void 0!==t.Ot}function te(t,i){return void 0!==i.customValues&&(t.jb=i.customValues),t}function ie(t){return(i,n,s,e,r,h)=>function(t,i){return i?i(t):void 0===(n=t).open&&void 0===n.value;var n}(s,h)?te({ot:i,ee:n,Eb:e},s):te(t(i,n,s,e,r),s)}function ne(t){return{Candlestick:ie(Gs),Bar:ie(Ks),Area:ie(Zs),Baseline:ie(Xs),Histogram:ie(Ys),Line:ie(Ys),Custom:ie(Js)}[t]}function se(t){return{ee:0,Hb:new Map,la:t}}function ee(t,i){if(void 0!==t&&0!==t.length)return{$b:i.key(t[0].ot),Ub:i.key(t[t.length-1].ot)}}function re(t){let i;return t.forEach((t=>{void 0===i&&(i=t.Eb)})),d(i)}class he{constructor(t){this.qb=new Map,this.Yb=new Map,this.Zb=new Map,this.Xb=[],this.q_=t}S(){this.qb.clear(),this.Yb.clear(),this.Zb.clear(),this.Xb=[]}Kb(t,i){let n=0!==this.qb.size,s=!1;const e=this.Yb.get(t);if(void 0!==e)if(1===this.Yb.size)n=!1,s=!0,this.qb.clear();else for(const i of this.Xb)i.pointData.Hb.delete(t)&&(s=!0);let r=[];if(0!==i.length){const n=i.map((t=>t.time)),e=this.q_.createConverterToInternalObj(i),h=ne(t.Qh()),l=t.Ca(),a=t.Ta();r=i.map(((i,r)=>{const o=e(i.time),_=this.q_.key(o);let u=this.qb.get(_);void 0===u&&(u=se(o),this.qb.set(_,u),s=!0);const c=h(o,u.ee,i,n[r],l,a);return u.Hb.set(t,c),c}))}n&&this.Gb(),this.Jb(t,r);let h=-1;if(s){const t=[];this.qb.forEach((i=>{t.push({timeWeight:0,time:i.la,pointData:i,originalTime:re(i.Hb)})})),t.sort(((t,i)=>this.q_.key(t.time)-this.q_.key(i.time))),h=this.Qb(t)}return this.tw(t,h,function(t,i,n){const s=ee(t,n),e=ee(i,n);if(void 0!==s&&void 0!==e)return{ta:s.Ub>=e.Ub&&s.$b>=e.$b}}(this.Yb.get(t),e,this.q_))}vd(t){return this.Kb(t,[])}iw(t,i){const n=i;!function(t){void 0===t.Eb&&(t.Eb=t.time)}(n),this.q_.preprocessData(i);const s=this.q_.createConverterToInternalObj([i])(i.time),e=this.Zb.get(t);if(void 0!==e&&this.q_.key(s)<this.q_.key(e))throw new Error(`Cannot update oldest data, last time=${e}, new time=${s}`);let r=this.qb.get(this.q_.key(s));const h=void 0===r;void 0===r&&(r=se(s),this.qb.set(this.q_.key(s),r));const l=ne(t.Qh()),a=t.Ca(),o=t.Ta(),_=l(s,r.ee,i,n.Eb,a,o);r.Hb.set(t,_),this.nw(t,_);const u={ta:Qs(_)};if(!h)return this.tw(t,-1,u);const c={timeWeight:0,time:r.la,pointData:r,originalTime:re(r.Hb)},d=Rt(this.Xb,this.q_.key(c.time),((t,i)=>this.q_.key(t.time)<i));this.Xb.splice(d,0,c);for(let t=d;t<this.Xb.length;++t)le(this.Xb[t].pointData,t);return this.q_.fillWeightsForPoints(this.Xb,d),this.tw(t,d,u)}nw(t,i){let n=this.Yb.get(t);void 0===n&&(n=[],this.Yb.set(t,n));const s=0!==n.length?n[n.length-1]:null;null===s||this.q_.key(i.ot)>this.q_.key(s.ot)?Qs(i)&&n.push(i):Qs(i)?n[n.length-1]=i:n.splice(-1,1),this.Zb.set(t,i.ot)}Jb(t,i){0!==i.length?(this.Yb.set(t,i.filter(Qs)),this.Zb.set(t,i[i.length-1].ot)):(this.Yb.delete(t),this.Zb.delete(t))}Gb(){for(const t of this.Xb)0===t.pointData.Hb.size&&this.qb.delete(this.q_.key(t.time))}Qb(t){let i=-1;for(let n=0;n<this.Xb.length&&n<t.length;++n){const s=this.Xb[n],e=t[n];if(this.q_.key(s.time)!==this.q_.key(e.time)){i=n;break}e.timeWeight=s.timeWeight,le(e.pointData,n)}if(-1===i&&this.Xb.length!==t.length&&(i=Math.min(this.Xb.length,t.length)),-1===i)return-1;for(let n=i;n<t.length;++n)le(t[n].pointData,n);return this.q_.fillWeightsForPoints(t,i),this.Xb=t,i}sw(){if(0===this.Yb.size)return null;let t=0;return this.Yb.forEach((i=>{0!==i.length&&(t=Math.max(t,i[i.length-1].ee))})),t}tw(t,i,n){const s={ew:new Map,St:{Lu:this.sw()}};if(-1!==i)this.Yb.forEach(((i,e)=>{s.ew.set(e,{$e:i,rw:e===t?n:void 0})})),this.Yb.has(t)||s.ew.set(t,{$e:[],rw:n}),s.St.hw=this.Xb,s.St.lw=i;else{const i=this.Yb.get(t);s.ew.set(t,{$e:i||[],rw:n})}return s}}function le(t,i){t.ee=i,t.Hb.forEach((t=>{t.ee=i}))}function ae(t){const i={value:t.Ot[3],time:t.Eb};return void 0!==t.jb&&(i.customValues=t.jb),i}function oe(t){const i=ae(t);return void 0!==t.O&&(i.color=t.O),i}function _e(t){const i=ae(t);return void 0!==t.lt&&(i.lineColor=t.lt),void 0!==t.Ps&&(i.topColor=t.Ps),void 0!==t.Rs&&(i.bottomColor=t.Rs),i}function ue(t){const i=ae(t);return void 0!==t.Re&&(i.topLineColor=t.Re),void 0!==t.De&&(i.bottomLineColor=t.De),void 0!==t.ke&&(i.topFillColor1=t.ke),void 0!==t.ye&&(i.topFillColor2=t.ye),void 0!==t.Ce&&(i.bottomFillColor1=t.Ce),void 0!==t.Te&&(i.bottomFillColor2=t.Te),i}function ce(t){const i={open:t.Ot[0],high:t.Ot[1],low:t.Ot[2],close:t.Ot[3],time:t.Eb};return void 0!==t.jb&&(i.customValues=t.jb),i}function de(t){const i=ce(t);return void 0!==t.O&&(i.color=t.O),i}function fe(t){const i=ce(t),{O:n,Bt:s,Xh:e}=t;return void 0!==n&&(i.color=n),void 0!==s&&(i.borderColor=s),void 0!==e&&(i.wickColor=e),i}function ve(t){return{Area:_e,Line:oe,Baseline:ue,Histogram:oe,Bar:de,Candlestick:fe,Custom:pe}[t]}function pe(t){const i=t.Eb;return Object.assign(Object.assign({},t.$e),{time:i})}const me={vertLine:{color:\"#9598A1\",width:1,style:3,visible:!0,labelVisible:!0,labelBackgroundColor:\"#131722\"},horzLine:{color:\"#9598A1\",width:1,style:3,visible:!0,labelVisible:!0,labelBackgroundColor:\"#131722\"},mode:1},be={vertLines:{color:\"#D6DCDE\",style:0,visible:!0},horzLines:{color:\"#D6DCDE\",style:0,visible:!0}},we={background:{type:\"solid\",color:\"#FFFFFF\"},textColor:\"#191919\",fontSize:12,fontFamily:z,attributionLogo:!0},ge={autoScale:!0,mode:0,invertScale:!1,alignLabels:!0,borderVisible:!0,borderColor:\"#2B2B43\",entireTextOnly:!1,visible:!1,ticksVisible:!1,scaleMargins:{bottom:.1,top:.2},minimumWidth:0},Me={rightOffset:0,barSpacing:6,minBarSpacing:.5,fixLeftEdge:!1,fixRightEdge:!1,lockVisibleTimeRangeOnResize:!1,rightBarStaysOnScroll:!1,borderVisible:!0,borderColor:\"#2B2B43\",visible:!0,timeVisible:!1,secondsVisible:!0,shiftVisibleRangeOnNewBar:!0,allowShiftVisibleRangeOnWhitespaceReplacement:!1,ticksVisible:!1,uniformDistribution:!1,minimumHeight:0,allowBoldLabels:!0},xe={color:\"rgba(0, 0, 0, 0)\",visible:!1,fontSize:48,fontFamily:z,fontStyle:\"\",text:\"\",horzAlign:\"center\",vertAlign:\"center\"};function Se(){return{width:0,height:0,autoSize:!1,layout:we,crosshair:me,grid:be,overlayPriceScales:Object.assign({},ge),leftPriceScale:Object.assign(Object.assign({},ge),{visible:!1}),rightPriceScale:Object.assign(Object.assign({},ge),{visible:!0}),timeScale:Me,watermark:xe,localization:{locale:rs?navigator.language:\"\",dateFormat:\"dd MMM 'yy\"},handleScroll:{mouseWheel:!0,pressedMouseMove:!0,horzTouchDrag:!0,vertTouchDrag:!0},handleScale:{axisPressedMouseMove:{time:!0,price:!0},axisDoubleClickReset:{time:!0,price:!0},mouseWheel:!0,pinch:!0},kineticScroll:{mouse:!1,touch:!0},trackingMode:{exitMode:1}}}class ke{constructor(t,i){this.aw=t,this.ow=i}applyOptions(t){this.aw.$t().$c(this.ow,t)}options(){return this.Ii().W()}width(){return ht(this.ow)?this.aw.Mb(this.ow):0}Ii(){return f(this.aw.$t().Uc(this.ow)).Dt}}function ye(t,i,n){const s=qs(t,[\"time\",\"originalTime\"]),e=Object.assign({time:i},s);return void 0!==n&&(e.originalTime=n),e}const Ce={color:\"#FF0000\",price:0,lineStyle:2,lineWidth:1,lineVisible:!0,axisLabelVisible:!0,title:\"\",axisLabelColor:\"\",axisLabelTextColor:\"\"};class Te{constructor(t){this.Nh=t}applyOptions(t){this.Nh.$h(t)}options(){return this.Nh.W()}_w(){return this.Nh}}class Pe{constructor(t,i,n,s,e){this.uw=new C,this.Ls=t,this.cw=i,this.dw=n,this.q_=e,this.fw=s}S(){this.uw.S()}priceFormatter(){return this.Ls.ba()}priceToCoordinate(t){const i=this.Ls.Ct();return null===i?null:this.Ls.Dt().Rt(t,i.Ot)}coordinateToPrice(t){const i=this.Ls.Ct();return null===i?null:this.Ls.Dt().pn(t,i.Ot)}barsInLogicalRange(t){if(null===t)return null;const i=new Mn(new bn(t.from,t.to)).lu(),n=this.Ls.zn();if(n.Ni())return null;const s=n.ll(i.Bs(),1),e=n.ll(i.ui(),-1),r=f(n.el()),h=f(n.An());if(null!==s&&null!==e&&s.ee>e.ee)return{barsBefore:t.from-r,barsAfter:h-t.to};const l={barsBefore:null===s||s.ee===r?t.from-r:s.ee-r,barsAfter:null===e||e.ee===h?h-t.to:h-e.ee};return null!==s&&null!==e&&(l.from=s.Eb,l.to=e.Eb),l}setData(t){this.q_,this.Ls.Qh(),this.cw.pw(this.Ls,t),this.mw(\"full\")}update(t){this.Ls.Qh(),this.cw.bw(this.Ls,t),this.mw(\"update\")}dataByIndex(t,i){const n=this.Ls.zn().ll(t,i);if(null===n)return null;return ve(this.seriesType())(n)}data(){const t=ve(this.seriesType());return this.Ls.zn().ne().map((i=>t(i)))}subscribeDataChanged(t){this.uw.l(t)}unsubscribeDataChanged(t){this.uw.v(t)}setMarkers(t){this.q_;const i=t.map((t=>ye(t,this.q_.convertHorzItemToInternal(t.time),t.time)));this.Ls.na(i)}markers(){return this.Ls.sa().map((t=>ye(t,t.originalTime,void 0)))}applyOptions(t){this.Ls.$h(t)}options(){return B(this.Ls.W())}priceScale(){return this.dw.priceScale(this.Ls.Dt().Pa())}createPriceLine(t){const i=T(B(Ce),t),n=this.Ls.ea(i);return new Te(n)}removePriceLine(t){this.Ls.ra(t._w())}seriesType(){return this.Ls.Qh()}attachPrimitive(t){this.Ls.ka(t),t.attached&&t.attached({chart:this.fw,series:this,requestUpdate:()=>this.Ls.$t().Kl()})}detachPrimitive(t){this.Ls.ya(t),t.detached&&t.detached()}mw(t){this.uw.M()&&this.uw.m(t)}}class Re{constructor(t,i,n){this.ww=new C,this.mu=new C,this.Bm=new C,this.$i=t,this.yl=t.St(),this.ab=i,this.yl.nc().l(this.gw.bind(this)),this.yl.sc().l(this.Mw.bind(this)),this.ab.Nm().l(this.xw.bind(this)),this.q_=n}S(){this.yl.nc().p(this),this.yl.sc().p(this),this.ab.Nm().p(this),this.ww.S(),this.mu.S(),this.Bm.S()}scrollPosition(){return this.yl.Hu()}scrollToPosition(t,i){i?this.yl.Ju(t,1e3):this.$i.Jn(t)}scrollToRealTime(){this.yl.Gu()}getVisibleRange(){const t=this.yl.Ou();return null===t?null:{from:t.from.originalTime,to:t.to.originalTime}}setVisibleRange(t){const i={from:this.q_.convertHorzItemToInternal(t.from),to:this.q_.convertHorzItemToInternal(t.to)},n=this.yl.zu(i);this.$i.pd(n)}getVisibleLogicalRange(){const t=this.yl.Du();return null===t?null:{from:t.Bs(),to:t.ui()}}setVisibleLogicalRange(t){c(t.from<=t.to,\"The from index cannot be after the to index.\"),this.$i.pd(t)}resetTimeScale(){this.$i.Kn()}fitContent(){this.$i.hc()}logicalToCoordinate(t){const i=this.$i.St();return i.Ni()?null:i.zt(t)}coordinateToLogical(t){return this.yl.Ni()?null:this.yl.Nu(t)}timeToCoordinate(t){const i=this.q_.convertHorzItemToInternal(t),n=this.yl.Oa(i,!1);return null===n?null:this.yl.zt(n)}coordinateToTime(t){const i=this.$i.St(),n=i.Nu(t),s=i.Ui(n);return null===s?null:s.originalTime}width(){return this.ab.um().width}height(){return this.ab.um().height}subscribeVisibleTimeRangeChange(t){this.ww.l(t)}unsubscribeVisibleTimeRangeChange(t){this.ww.v(t)}subscribeVisibleLogicalRangeChange(t){this.mu.l(t)}unsubscribeVisibleLogicalRangeChange(t){this.mu.v(t)}subscribeSizeChange(t){this.Bm.l(t)}unsubscribeSizeChange(t){this.Bm.v(t)}applyOptions(t){this.yl.$h(t)}options(){return Object.assign(Object.assign({},B(this.yl.W())),{barSpacing:this.yl.le()})}gw(){this.ww.M()&&this.ww.m(this.getVisibleRange())}Mw(){this.mu.M()&&this.mu.m(this.getVisibleLogicalRange())}xw(t){this.Bm.m(t.width,t.height)}}function De(t){if(void 0===t||\"custom\"===t.type)return;const i=t;void 0!==i.minMove&&void 0===i.precision&&(i.precision=function(t){if(t>=1)return 0;let i=0;for(;i<8;i++){const n=Math.round(t);if(Math.abs(n-t)<1e-8)return i;t*=10}return i}(i.minMove))}function Oe(t){return function(t){if(O(t.handleScale)){const i=t.handleScale;t.handleScale={axisDoubleClickReset:{time:i,price:i},axisPressedMouseMove:{time:i,price:i},mouseWheel:i,pinch:i}}else if(void 0!==t.handleScale){const{axisPressedMouseMove:i,axisDoubleClickReset:n}=t.handleScale;O(i)&&(t.handleScale.axisPressedMouseMove={time:i,price:i}),O(n)&&(t.handleScale.axisDoubleClickReset={time:n,price:n})}const i=t.handleScroll;O(i)&&(t.handleScroll={horzTouchDrag:i,vertTouchDrag:i,mouseWheel:i,pressedMouseMove:i})}(t),t}class Be{constructor(t,i,n){this.Sw=new Map,this.kw=new Map,this.yw=new C,this.Cw=new C,this.Tw=new C,this.Pw=new he(i);const s=void 0===n?B(Se()):T(B(Se()),Oe(n));this.q_=i,this.aw=new Hs(t,s,i),this.aw.lm().l((t=>{this.yw.M()&&this.yw.m(this.Rw(t()))}),this),this.aw.am().l((t=>{this.Cw.M()&&this.Cw.m(this.Rw(t()))}),this),this.aw.Xc().l((t=>{this.Tw.M()&&this.Tw.m(this.Rw(t()))}),this);const e=this.aw.$t();this.Dw=new Re(e,this.aw.fb(),this.q_)}remove(){this.aw.lm().p(this),this.aw.am().p(this),this.aw.Xc().p(this),this.Dw.S(),this.aw.S(),this.Sw.clear(),this.kw.clear(),this.yw.S(),this.Cw.S(),this.Tw.S(),this.Pw.S()}resize(t,i,n){this.autoSizeActive()||this.aw._b(t,i,n)}addCustomSeries(t,i){const n=v(t),s=Object.assign(Object.assign({},h),n.defaultOptions());return this.Ow(\"Custom\",s,i,n)}addAreaSeries(t){return this.Ow(\"Area\",s,t)}addBaselineSeries(t){return this.Ow(\"Baseline\",e,t)}addBarSeries(t){return this.Ow(\"Bar\",i,t)}addCandlestickSeries(i={}){return function(t){void 0!==t.borderColor&&(t.borderUpColor=t.borderColor,t.borderDownColor=t.borderColor),void 0!==t.wickColor&&(t.wickUpColor=t.wickColor,t.wickDownColor=t.wickColor)}(i),this.Ow(\"Candlestick\",t,i)}addHistogramSeries(t){return this.Ow(\"Histogram\",r,t)}addLineSeries(t){return this.Ow(\"Line\",n,t)}removeSeries(t){const i=d(this.Sw.get(t)),n=this.Pw.vd(i);this.aw.$t().vd(i),this.Bw(n),this.Sw.delete(t),this.kw.delete(i)}pw(t,i){this.Bw(this.Pw.Kb(t,i))}bw(t,i){this.Bw(this.Pw.iw(t,i))}subscribeClick(t){this.yw.l(t)}unsubscribeClick(t){this.yw.v(t)}subscribeCrosshairMove(t){this.Tw.l(t)}unsubscribeCrosshairMove(t){this.Tw.v(t)}subscribeDblClick(t){this.Cw.l(t)}unsubscribeDblClick(t){this.Cw.v(t)}priceScale(t){return new ke(this.aw,t)}timeScale(){return this.Dw}applyOptions(t){this.aw.$h(Oe(t))}options(){return this.aw.W()}takeScreenshot(){return this.aw.wb()}autoSizeActive(){return this.aw.kb()}chartElement(){return this.aw.yb()}paneSize(){const t=this.aw.Tb();return{height:t.height,width:t.width}}setCrosshairPosition(t,i,n){const s=this.Sw.get(n);if(void 0===s)return;const e=this.aw.$t().dr(s);null!==e&&this.aw.$t().ad(t,i,e)}clearCrosshairPosition(){this.aw.$t().od(!0)}Ow(t,i,n={},s){De(n.priceFormat);const e=T(B(l),B(i),n),r=this.aw.$t().dd(t,e,s),h=new Pe(r,this,this,this,this.q_);return this.Sw.set(h,r),this.kw.set(r,h),h}Bw(t){const i=this.aw.$t();i._d(t.St.Lu,t.St.hw,t.St.lw),t.ew.forEach(((t,i)=>i.J(t.$e,t.rw))),i.Wu()}Vw(t){return d(this.kw.get(t))}Rw(t){const i=new Map;t.Nb.forEach(((t,n)=>{const s=n.Qh(),e=ve(s)(t);if(\"Custom\"!==s)c(Us(e));else{const t=n.Ta();c(!t||!1===t(e))}i.set(this.Vw(n),e)}));const n=void 0!==t.Lb&&this.kw.has(t.Lb)?this.Vw(t.Lb):void 0;return{time:t.Eb,logical:t.ee,point:t.Ib,hoveredSeries:n,hoveredObjectId:t.Fb,seriesData:i,sourceEvent:t.Wb}}}function Ve(t,i,n){let s;if(D(t)){const i=document.getElementById(t);c(null!==i,`Cannot find element in DOM with id=${t}`),s=i}else s=t;const e=new Be(s,i,n);return i.setOptions(e.options()),e}const Ae=Object.assign(Object.assign({},l),h);var ze=Object.freeze({__proto__:null,get ColorType(){return On},get CrosshairMode(){return et},get LastPriceAnimationMode(){return Rn},get LineStyle(){return o},get LineType(){return a},get MismatchDirection(){return Vi},get PriceLineSource(){return Dn},get PriceScaleMode(){return cn},get TickMarkType(){return Bn},get TrackingModeExitMode(){return Pn},createChart:function(t,i){return Ve(t,new Gn,Gn.zd(i))},createChartEx:Ve,customSeriesDefaultOptions:Ae,defaultHorzScaleBehavior:function(){return Gn},isBusinessDay:An,isUTCTimestamp:zn,version:function(){return\"4.2.3\"}});window.LightweightCharts=ze}();\n"

BG="#080F18"; PANEL="#102735"; PANEL2="#12313E"; GOLD="#E9B949"; GREEN="#16C784"; RED="#FF7890"; WHITE="#EAF1F6"; MUTED="#A9BBC5"; BORDER="#718796"
STATE,CACHE_FILE=storage_paths()

def app_main(page:ft.Page):
    page.title="BOT KING"; page.theme_mode=ft.ThemeMode.DARK; page.bgcolor=BG; page.padding=0; page.spacing=0
    page.window_width=420; page.window_height=850
    page.dark_theme=ft.Theme(color_scheme=ft.ColorScheme(primary=GOLD,on_primary=BG,secondary=GOLD,on_secondary=BG,surface=PANEL,on_surface=WHITE,error=RED,on_error=BG,outline=BORDER))
    prefs={"mode":"Paper","stop_loss":2.0,"target":4.0,"max_trades":2,"confidence":75,"source":"Dhan","api_url":"","api_key":""}
    prefs.update(load_preferences(STATE,page.client_storage))
    if prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):prefs["source"]="Dhan"
    prefs["schema_version"]=2
    if prefs.get("language") not in ("English","हिंदी"):prefs["language"]="English"
    original_page_update=page.update
    def localized_update(*args,**kwargs):
        with view_lock:
            for root in page.controls:localize_tree(root,prefs.get("language","English"))
            return original_page_update(*args,**kwargs)
    page.update=localized_update
    diagnostics=[]
    dhan_batch_issue=[None]  # Active batch failure; cleared only after a verified batch succeeds.
    from threading import RLock
    trade_lock=RLock()
    view_lock=RLock()
    scan_generation=[0]
    provider_generation=[0]
    angel_feed=ServerAngelFeed()
    dhan_feed=ServerDhanReadOnly()
    broker_retry=[0.0]
    broker_failures=[0]
    health=FeedHealth()
    scan_progress={"checked":0,"total":51,"valid":0,"failed":0,"cached":0,"state":"Waiting"}
    failed_symbols={}
    app_active=[True]
    lifecycle_background=[False]
    resume_busy=[False]
    runtime_status=ft.Text("While-open monitoring only; screen-lock continuity is not verified",size=12,color=MUTED)
    option_feed={}
    option_feed_busy=[False]
    broker_connect_busy=[False]
    option_feed_status=["Dhan option metrics not loaded; live orders OFF."]
    dhan_option_metrics={}
    dhan_option_last_attempt=[0.0]
    def log_error(area,exc):
        # Store only exception types; never endpoint URLs, credentials or response bodies.
        diagnostics.append(datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M:%S IST")+" "+area+": "+type(exc).__name__)
        del diagnostics[:-30]
    def regular_hours(now=None):
        now=now or datetime.now(timezone(timedelta(hours=5,minutes=30)))
        return now.weekday()<5 and (9,15)<=(now.hour,now.minute)<(15,30)
    def session_caption():
        return ("Regular session hours • exchange holidays not verified" if regular_hours()
                else "Outside regular session hours • automatic refresh paused")
    market_store=SnapshotStore(CACHE_FILE)
    # Legacy Yahoo snapshots must not be shown as Angel One market data.
    quotes={symbol:row for symbol,row in market_store.latest_markets().items() if row.get("source")==({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan"))}
    candles={}
    news_cache={}
    for cache_key in (prefs.get("scanner_symbol","NIFTY"),"GLOBAL"):
        previous_news=market_store.get("news",cache_key)
        if previous_news:news_cache[cache_key]=previous_news
    fusion_cache={}
    fusion_selected=ft.Column(spacing=5)
    option_snapshots={}  # Populated only by a future authenticated broker adapter, never by simulated premiums.
    news_lock=RLock()
    company_names={"NIFTY":"Nifty India markets","BANKNIFTY":"Indian bank stocks","SENSEX":"Sensex India markets","HDFCBANK":"HDFC Bank","SBIN":"State Bank of India","ICICIBANK":"ICICI Bank","RELIANCE":"Reliance Industries","TCS":"Tata Consultancy Services","INFY":"Infosys"}
    filter_modes=prefs.setdefault("filter_modes",{})
    for name in list(filter_modes):
        if name!="EMA 9/21" or filter_modes[name] not in ("Analysis","Chart","Both"):filter_modes[name]="Analysis"
    filter_modes.setdefault("EMA 9/21","Both" if "EMA 9/21" in prefs.get("scanner_chart_indicators",["EMA 9/21"]) else "Analysis")
    def active_analysis_filters():
        return [name for name in filter_selected if filter_modes.get(name,"Analysis")!="Chart"]
    def ema_on_chart():
        return "EMA 9/21" in filter_selected and filter_modes.get("EMA 9/21","Both") in ("Chart","Both")
    def parse_news_rss(raw,source):
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        if len(raw)>2_000_000 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():raise ValueError("Unsupported news XML")
        now=datetime.now(timezone.utc).timestamp();items=[];seen=set()
        root=ET.fromstring(raw)
        for node in root.findall("./channel/item"):
            title=" ".join((node.findtext("title") or "").split())[:350]
            url=(node.findtext("link") or "").strip()
            try:
                stamp=parsedate_to_datetime(node.findtext("pubDate") or "")
                if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=timezone.utc)
                ts=stamp.timestamp()
            except (TypeError,ValueError,OverflowError):continue
            if not title or not url.startswith("https://") or not 0<=now-ts<=86400 or title.lower() in seen:continue
            seen.add(title.lower())
            publisher=node.findtext("source") or source
            items.append({"title":title,"url":url,"published":ts,"source":publisher[:100]})
        return sorted(items,key=lambda x:x["published"],reverse=True)[:20]
    def fetch_news(symbol,global_news=False):
        key="GLOBAL" if global_news else symbol
        now=datetime.now(timezone.utc).timestamp()
        health_key="news:"+key;request_id=health.begin(health_key)
        with news_lock:
            cached=news_cache.get(key) or market_store.get("news",key)
            if cached and now-cached["fetched"]<600:
                health.finish(health_key,request_id,"CACHED",source=cached.get("source","RSS"),data_time=max([r.get("published",0) for r in cached.get("items",[])]+[0]))
                return cached
        if global_news:
            url="https://feeds.bbci.co.uk/news/business/rss.xml";source_name="BBC News Business"
        else:
            name=company_names.get(symbol,symbol)
            query='"'+name+'" stock when:1d' if symbol not in ("NIFTY","BANKNIFTY","SENSEX") else name+' when:1d'
            url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":query,"hl":"en-IN","gl":"IN","ceid":"IN:en"})
            source_name="Google News RSS — linked publishers"
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 BOT KING personal headline reader"})
            with urllib.request.urlopen(request,timeout=8) as response:raw=response.read(2_000_001)
            items=parse_news_rss(raw,source_name)
            result={"items":items,"fetched":now,"status":"Available" if items else "No recent headlines","source":source_name}
        except Exception as exc:
            log_error("news",exc)
            result={"items":[],"fetched":now,"status":"Unavailable ("+type(exc).__name__+")","source":source_name}
        if result.get("items"):market_store.put("news",(key,),result)
        elif cached and cached.get("items"):
            result=dict(cached,status="Cached headlines • "+age_label(max(x.get("published",0) for x in cached["items"])))
        health.finish(health_key,request_id,"AVAILABLE" if result.get("items") and result.get("fetched")==now else "CACHED" if result.get("items") else "UNAVAILABLE",source=result.get("source","RSS"),data_time=max([r.get("published",0) for r in result.get("items",[])]+[0]),error="" if result.get("items") else "No recent headlines or feed unavailable")
        with news_lock:news_cache[key]=result
        return result
    def headline_signal(items):
        # Cautious headline cues, not a contextual language model or verified market impact.
        import re
        positive=("profit rises","profit jumps","profit surges","raises guidance","record profit","wins contract","upgrade","beats estimates","loss narrows")
        negative=("profit falls","profit drops","cuts guidance","fraud","downgrade","misses estimates","loss widens","default on")
        pos=neg=0
        for item in items:
            text=item["title"].lower()
            if re.search(r"(not|denies|denied|rumour|rumor|may|could)",text):continue
            up=any(term in text for term in positive);down=any(term in text for term in negative)
            if up and not down:pos+=1
            elif down and not up:neg+=1
        bias="POSITIVE" if pos>=2 and neg==0 else "NEGATIVE" if neg>=2 and pos==0 else "MIXED" if pos and neg else "UNCLASSIFIED"
        return {"bias":bias,"positive":pos,"negative":neg,"method":"Experimental headline phrases; context and market impact not verified"}
    def option_component(symbol,interval):
        snap=option_snapshots.get(symbol)
        missing={"available":False,"bias":"UNAVAILABLE","reason":"Verified CE/PE feed not connected. Simulated premiums are excluded.","call_volume":None,"put_volume":None}
        if not snap:return missing
        try:
            age=datetime.now(timezone.utc).timestamp()-float(snap["timestamp"])
            if snap.get("symbol")!=symbol or snap.get("timeframe")!=interval or not snap.get("verified") or not 0<=age<=timeframe_spec(interval)["fresh_seconds"]:return missing
            # Volume/OI alone cannot establish bullish or bearish intent.
            direction=snap.get("direction") if snap.get("direction_basis")=="validated_trade_flow" else "UNCONFIRMED"
            if direction not in ("BULLISH","BEARISH"):direction="UNCONFIRMED"
            return {"available":True,"bias":direction,"reason":"Volume/OI are activity, not investor profits. Direction requires validated buy/sell flow.","call_volume":snap.get("call_volume"),"put_volume":snap.get("put_volume"),"call_turnover":snap.get("call_turnover"),"put_turnover":snap.get("put_turnover"),"expiry":snap.get("expiry"),"source":snap.get("source","Broker"),"timestamp":snap["timestamp"]}
        except (KeyError,ValueError,TypeError,OverflowError):return missing
    def combine_analysis(symbol,interval,candle,local_news,global_news):
        now=datetime.now(timezone.utc).timestamp()
        aliases={"NIFTY":["nifty"],"BANKNIFTY":["bank nifty","banknifty"],"SENSEX":["sensex"],"HDFCBANK":["hdfc bank"],"SBIN":["state bank of india","sbi"],"ICICIBANK":["icici bank"],"RELIANCE":["reliance industries","reliance"],"TCS":["tata consultancy","tcs"],"INFY":["infosys"]}.get(symbol,[symbol.lower()])
        import re
        def matches(title):return any(re.search(r"(?<!\w)"+re.escape(alias)+r"(?!\w)",title,re.I) for alias in aliases)
        items=[x for x in local_news.get("items",[]) if 0<=now-x.get("published",0)<=86400 and matches(x.get("title",""))]
        cues=headline_signal(items);options=option_component(symbol,interval)
        candle_age=now-(candle.get("timestamp") or 0)
        candle_valid=not candle.get("historical") and not candle.get("cached") and 0<=candle_age<=timeframe_spec(interval)["fresh_seconds"] and candle.get("bias") in ("BULLISH","BEARISH")
        news_bias={"POSITIVE":"BULLISH","NEGATIVE":"BEARISH"}.get(cues["bias"])
        votes=[candle.get("bias") if candle_valid else None,options["bias"] if options["available"] and options["bias"] in ("BULLISH","BEARISH") else None,news_bias]
        complete=all(v is not None for v in votes)
        overall=votes[0] if complete and len(set(votes))==1 else "WAIT"
        reason=("Experimental three-source agreement; not a win probability" if overall!="WAIT" else "Incomplete inputs or conflicting directions; no confirmed combined setup")
        return {"symbol":symbol,"timeframe":interval,"overall":overall,"coverage":sum(v is not None for v in votes),"reason":reason,"candle":candle,"options":options,"news":cues,"headlines":items[:5],"global_headlines":[x for x in global_news.get("items",[]) if 0<=now-x.get("published",0)<=86400][:3],"news_status":local_news.get("status","Unavailable") if items else "No recent matching headlines / feed unavailable","global_status":global_news.get("status","Unavailable"),"timestamp":now}
    async def load_combined(symbol,interval,candle):
        local_news,world_news=await asyncio.gather(asyncio.to_thread(fetch_news,symbol),asyncio.to_thread(fetch_news,symbol,True))
        result=combine_analysis(symbol,interval,candle,local_news,world_news)
        if not candle.get("historical") and candle.get("timestamp"):
            market_store.put("fusion",(symbol,interval),result)
        return result
    def fusion_card(symbol,interval,compact=False):
        data=fusion_cache.get(symbol+":"+interval) or market_store.get("fusion",symbol,interval)
        if not data:
            candle_note=("Candles: "+scan_shared["direction"]+" • "+scan_shared["basis"] if scan_shared.get("symbol")==symbol and scan_shared.get("tf")==interval else "Candle analysis not available for this selection yet")
            return section("COMBINED ANALYSIS • "+symbol,ft.Column([note(candle_note),note("News analysis pending or unavailable. Options require a verified broker feed.")],spacing=5))
        data=dict(data)
        combined_age=datetime.now(timezone.utc).timestamp()-(data.get("timestamp") or 0)
        if combined_age<0 or combined_age>timeframe_spec(interval)["fresh_seconds"]:
            previous_direction=data.get("overall","WAIT")
            data.update(overall="WAIT",reason="HISTORICAL combined result: "+age_label(data.get("timestamp"))+
                        " • previous direction "+previous_direction+" is not a current signal. "+data.get("reason",""))
        controls=[txt(data["overall"]+" • "+str(data["coverage"])+"/3 directional inputs",16,GOLD,True),
            note("Candles: "+data["candle"]["bias"]+" | Options: "+data["options"]["bias"]+" | News cues: "+data["news"]["bias"]),note(data["reason"])]
        if not compact:
            controls.extend([note("Candle time (IST): "+(datetime.fromtimestamp(data["candle"]["timestamp"],timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M") if data["candle"].get("timestamp") else "Unavailable")),
                note(data["options"]["reason"]),note(data["news"]["method"]),note("Local/company news: "+data["news_status"]+" | Global business: "+data["global_status"]),note("Global headlines are context only; positive for one sector may be negative for another.")])
            if data["options"]["available"]:
                controls.append(note("Call/Put volume: "+str(data["options"].get("call_volume"))+" / "+str(data["options"].get("put_volume"))+" contracts. Investor P&L is unknown."))
            for item in data["headlines"]+data["global_headlines"]:
                when=datetime.fromtimestamp(item["published"],timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M IST")
                controls.append(ft.Column([note(item["source"]+" • "+when),ft.TextButton(content=ft.Text(item["title"],size=12,color=WHITE),on_click=lambda e,url=item["url"]:page.launch_url(url))],spacing=1))
        return section("CANDLE + OPTIONS + NEWS • "+symbol+" • "+interval,ft.Column(controls,spacing=5))
    market_status="Waiting for broker API connection…"
    symbols_yahoo={"NIFTY":"^NSEI","NIFTY 50":"^NSEI","BANKNIFTY":"^NSEBANK","BANK NIFTY":"^NSEBANK","SENSEX":"^BSESN","RELIANCE":"RELIANCE.NS","HDFCBANK":"HDFCBANK.NS","ICICIBANK":"ICICIBANK.NS","TCS":"TCS.NS","INFY":"INFY.NS","BHARTIARTL":"BHARTIARTL.NS","SBIN":"SBIN.NS","ITC":"ITC.NS"}
    def clean_bars(bars):
        import math
        rows={}
        for b in bars:
            try:
                t=int(b[0]);o,h,l,c=map(float,b[1:5]);v=float(b[5] or 0)
                if t>0 and all(math.isfinite(x) and x>0 for x in (o,h,l,c)) and l<=min(o,c)<=max(o,c)<=h and math.isfinite(v) and v>=0:
                    rows[t]=(t,o,h,l,c,v)
            except (ValueError,TypeError,IndexError,OverflowError):continue
        return [rows[t] for t in sorted(rows)]
    def aggregate_3m(bars):
        out={}
        for t,o,h,l,c,v in clean_bars(bars):
            local=datetime.fromtimestamp(t,timezone(timedelta(hours=5,minutes=30)))
            start=local.replace(hour=9,minute=15,second=0,microsecond=0).timestamp()
            bucket=int(start+((t-start)//180)*180)
            if bucket not in out:out[bucket]=[bucket,o,h,l,c,v]
            else:
                row=out[bucket];row[2]=max(row[2],h);row[3]=min(row[3],l);row[4]=c;row[5]+=v
        return list(out.values())
    market_recent={};market_locks={};market_registry_lock=RLock()
    dhan_batch_cache={"generation":None,"updated":0.0,"quotes":{}}
    dhan_batch_lock=RLock()
    def get_market_data(ticker,interval="5m",range_="1d"):
        import time,copy
        key=(provider_generation[0],angel_feed.epoch,dhan_feed.connected,prefs.get("source","Dhan"),ticker,interval,range_)
        with market_registry_lock:lock=market_locks.setdefault(key,RLock())
        with lock:
            cached=market_recent.get(key)
            # Share recent same-provider candle results across Chart and Scanner.
            # Historical candles remain explicitly unverified, never live quotes.
            ttl=90 if key[3]=="Dhan" else 10
            if cached and time.monotonic()-cached[0]<ttl:return copy.deepcopy(cached[1])
            result=fetch_market_data_uncached(ticker,interval,range_)
            if key[0]!=provider_generation[0]:raise RuntimeError("Obsolete market response")
            with market_registry_lock:
                market_recent[key]=(time.monotonic(),copy.deepcopy(result))
                for old in list(market_recent):
                    if time.monotonic()-market_recent[old][0]>(90 if old[3]=="Dhan" else 30):market_recent.pop(old,None)
            return result
    def fetch_market_data_uncached(ticker,interval="5m",range_="1d"):
        import time
        selected=prefs.get("source","Dhan")
        generation=provider_generation[0]
        result=None
        health_key="market:"+selected+":"+ticker+":"+interval
        request_id=health.begin(health_key)
        fallback_reason=""
        try:
            if selected=="Yahoo Finance":
                result=get_yahoo(ticker,interval,range_)
            elif selected=="Dhan":
                if not dhan_feed.connected:
                    raise FeedError("Dhan disconnected; reconnect with Server Access Key in Settings")
                if ticker not in DHAN_VERIFIED_SYMBOLS:
                    raise FeedError("Dhan mapping for "+str(ticker)[:32]+" not verified; no fabricated quote")
                if interval not in ("1m","5m","15m","1h"):
                    raise FeedError("Dhan chart interval not verified: "+str(interval))
                from datetime import timedelta
                today=datetime.now(timezone(timedelta(hours=5,minutes=30))).date()
                start=today-timedelta(days=2 if range_=="2d" else 5 if range_ in ("5d","7d","1mo","3mo") else 1)  # Scanner uses tested 2-day window
                candle_result=dhan_feed.intraday(ticker,{"1m":1,"5m":5,"15m":15,"1h":60}[interval],start,today)
                bars=clean_bars(candle_result["bars"])
                if not bars:raise FeedError("Dhan returned no verified candles")
                # Historical candles must not be presented as a verified live quote.
                if bars[-1][0]>time.time()+300:raise FeedError("Dhan candle timestamp is in the future")
                quote=None
                if ticker!="NIFTY":
                    with dhan_batch_lock:
                        if (dhan_batch_cache["generation"]==generation
                                and time.monotonic()-dhan_batch_cache["updated"]<90):
                            quote=dhan_batch_cache["quotes"].get(ticker)
                if quote is None and ticker=="NIFTY":
                    try:
                        quote=dhan_feed.quote(ticker)
                    except FeedError as exc:
                        # Historical chart remains available if index LTP is missing.
                        log_error("dhan_chart_ltp",exc)
                        quote=None
                # Equity quotes come from the dedicated batch poller. Never
                # turn a 51-symbol candle scan into 51 extra individual LTP
                # requests when the batch cache expires during scanning.
                result={"price":quote["price"] if quote else None,"change":None,"high":None,"low":None,
                        "bars":bars,"source":"Dhan","quote_timestamp":None,
                        "fetched_at":time.time(),
                        "freshness":"unverified" if quote else "historical_unverified",
                        "live_verified":False,
                        "time":datetime.now().strftime("%H:%M")}
            elif selected=="Broker API" and angel_feed.connected:
                try:
                    result=angel_feed.history(ticker,interval,range_)
                    broker_failures[0]=0;broker_retry[0]=0
                except Exception as exc:
                    broker_failures[0]+=1
                    broker_retry[0]=time.monotonic()+retry_delay(broker_failures[0])
                    fallback_reason=safe_error(exc)
                    raise
            if result is None:
                if selected=="Broker API":
                    raise FeedError("Broker API not connected; connect Angel One in Settings")
                raise FeedError("Unsupported market data provider: "+str(selected)[:32]+"; select Dhan in Settings")
            result["cached"]=False
        except Exception as exc:
            fallback_reason=safe_error(exc)
            health.finish(health_key,request_id,"UNAVAILABLE",source=selected,error=fallback_reason)
            raise
        if generation!=provider_generation[0] or prefs.get("source","Dhan")!=selected:
            raise RuntimeError("Provider changed while data was loading; obsolete response discarded.")
        if not result.get("cached"):market_store.put("market",(selected,ticker,interval,range_),result)
        state="CACHED" if result.get("cached") else "FALLBACK" if result.get("fallback") else "AVAILABLE"
        quote_time=result.get("quote_timestamp")
        if state not in ("CACHED",) and (not isinstance(quote_time,(int,float)) or not 0<=time.time()-quote_time<=90):
            # A closed-session candle history is not a failed live feed. Never
            # infer a live quote timestamp from the candle or fetch time.
            if result.get("bars") and not result.get("fallback"):
                # Successful historical candles are not a failed chart request.
                # Quote freshness remains unverified even during market hours.
                state="HISTORICAL"
                fallback_reason=fallback_reason or "Candles available • quote timestamp unverified; not verified live"
            else:
                state="STALE"
                fallback_reason=fallback_reason or "Quote time is old, missing or invalid; historical display only"
        # Record historical candle time when no verified quote timestamp exists.
        # Candle time must never certify live quote freshness.
        historical_time=None
        if result.get("bars"):
            try:
                historical_time=float(result["bars"][-1][0])
                if not 0<historical_time<=time.time()+300:
                    historical_time=None
            except (TypeError,ValueError,IndexError):
                historical_time=None
        health.finish(health_key,request_id,state,source=result.get("source",""),
                      data_time=quote_time if isinstance(quote_time,(int,float)) else historical_time,
                      error=fallback_reason)
        return result
    def timeframe_spec(interval):
        specs={
            "1m":(60,375,"3–10 minutes"),"3m":(180,125,"6–20 minutes"),
            "5m":(300,75,"10–30 minutes"),"15m":(900,25,"30–60 minutes"),
            "30m":(1800,12.5,"1–2 hours"),"1h":(3600,7,"1–3 hours"),
            "1d":(86400,1,"1 trading day")}
        seconds,bars_per_day,horizon=specs[interval]
        return {"seconds":seconds,"annual_bars":bars_per_day*252,
                "fresh_seconds":max(120,seconds*2+30),"horizon":horizon}
    def analyze_current(bars,selected=None,timeframe="5m"):
        selected=[name for name in (filter_selected if selected is None else selected) if filter_modes.get(name,"Analysis")!="Chart"]
        quality=quality_check(bars,timeframe_spec(timeframe)["seconds"])
        result=analyze(quality["bars"],selected,timeframe)
        result["quality"]={k:v for k,v in quality.items() if k!="bars"}
        result["agreement_detail"]=agreement_detail(result)
        if not quality["usable"]:
            return dict(result,bias="WAIT",score=0,reason=result["reason"]+" • Data quality: "+"; ".join(quality["reasons"]))
        fresh_seconds=timeframe_spec(timeframe)["fresh_seconds"]
        age=datetime.now(timezone.utc).timestamp()-(result.get("timestamp") or 0)
        if age<0 or age>fresh_seconds:
            reason="source timestamp is in the future" if age<0 else "last candle is too old for this timeframe; historical only"
            return dict(result,bias="WAIT",score=0,reason=result["reason"]+" • "+reason)
        if result.get("score",0)<float(prefs.get("confidence",75)):
            result=dict(result,bias="WAIT",score=0,reason=result["reason"]+" • below saved agreement threshold")
        return result
    def get_yahoo(ticker,interval="5m",range_="1d"):
        requested=interval
        if interval=="1D":interval="1d"
        if interval=="3m":interval="1m";range_="7d"
        if interval=="1m":range_="7d"
        code=symbols_yahoo.get(ticker,ticker+".NS")
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(code,safe="")+"?interval="+interval+"&range="+range_
        request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (BOT KING Market Preview)","Accept":"application/json"})
        try:
            with urllib.request.urlopen(request,timeout=9) as response:
                data=json.load(response)["chart"]["result"][0]
        except Exception:
            request=urllib.request.Request(url.replace("query1.finance.yahoo.com","query2.finance.yahoo.com"),headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(request,timeout=9) as response:
                data=json.load(response)["chart"]["result"][0]
        meta=data["meta"]
        vals=data["indicators"]["quote"][0]
        timestamps=data.get("timestamp",[])
        bars=[(t,o,h,l,cl,v) for t,o,h,l,cl,v in zip(timestamps,vals["open"],vals["high"],vals["low"],vals["close"],vals["volume"]) if None not in (o,h,l,cl)]
        bars=clean_bars(bars)
        if requested=="3m":bars=aggregate_3m(bars)
        price=meta.get("regularMarketPrice")
        # chartPreviousClose can be the start of a multi-day range, not yesterday.
        previous=meta.get("previousClose") or meta.get("regularMarketPreviousClose") or meta.get("chartPreviousClose")
        change=((price/previous-1)*100) if price is not None and previous else None
        return {"price":price,"change":change,"high":meta.get("regularMarketDayHigh"),"low":meta.get("regularMarketDayLow"),"bars":bars,"time":datetime.now().strftime("%H:%M"),"source":"Yahoo Finance","quote_timestamp":meta.get("regularMarketTime"),"fetched_at":datetime.now(timezone.utc).timestamp()}
    preference_writer=PreferenceWriter(page,STATE,int(prefs.get("_prefs_revision",0)),lambda exc:log_error("preferences",exc))
    def save():
        # Never call synchronous native clientStorage RPC from async refresh tasks.
        # Defense in depth: never persist pairing or broker secrets, even if
        # a future UI path accidentally inserts one into prefs.
        secret_fields={"api_key","api_secret","access_token","password","totp",
                       "pairing_key","server_access_key","server_access",
                       "botking_pairing_key","dhan_token","client_secret"}
        safe={k:v for k,v in prefs.items() if k not in secret_fields}
        result=preference_writer.save(safe)
        prefs["_prefs_revision"]=preference_writer.revision
        return result
    def txt(s,size=14,color=WHITE,bold=False):
        return ft.Text(str(s),size=size,color=color,weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL)
    def card(*children):
        return ft.Container(content=ft.Column(list(children),spacing=4,horizontal_alignment=ft.CrossAxisAlignment.STRETCH),bgcolor=PANEL,border_radius=10,padding=7,border=ft.border.all(1,BORDER))
    def heading(s):return txt(s,17,WHITE,True)
    def pill(s,selected=False):
        return ft.Container(content=txt(s,12,BG if selected else MUTED,selected),bgcolor=GOLD if selected else PANEL2,padding=ft.padding.symmetric(12,8),border_radius=20)
    def note(s):return txt(s,11,MUTED)
    def unavailable(s):return txt("DATA UNAVAILABLE — "+s,13,RED)
    def dhan_offline():
        return prefs.get("source")=="Dhan" and not dhan_feed.connected
    def quote_price(sym):
        q=None if dhan_offline() else quotes.get(sym)
        return f'{q["price"]:,.2f}' if q and q.get("price") is not None else "—"
    def quote_change(sym):
        q=None if dhan_offline() else quotes.get(sym)
        v=q.get("change") if q and q.get("provider_status")!="provider_data_unavailable" else None
        return f'{v:+.2f}%' if v is not None else "—"
    def price_color(sym):
        q=None if dhan_offline() else quotes.get(sym)
        v=q.get("change") if q and q.get("provider_status")!="provider_data_unavailable" else None
        return GREEN if v is not None and v>=0 else RED if v is not None else MUTED
    def tiny_chart(sym,snapshot=None):
        q=snapshot if snapshot is not None else (quotes.get(sym) or {})
        bars=q.get("bars") or []
        values=[b[4] for b in bars[-30:]]
        if len(values)<2:return note("Chart unavailable")
        lo,hi=min(values),max(values)
        spread=max(hi-lo,.001)
        points=[ft.LineChartDataPoint(i,(v-lo)/spread*100) for i,v in enumerate(values)]
        return ft.LineChart(data_series=[ft.LineChartData(data_points=points,stroke_width=2,color=price_color(sym),curved=False)],min_x=0,max_x=len(points)-1,min_y=-5,max_y=105,left_axis=ft.ChartAxis(labels_size=0),bottom_axis=ft.ChartAxis(labels_size=0),right_axis=ft.ChartAxis(labels_size=0),top_axis=ft.ChartAxis(labels_size=0),border=ft.border.all(0,"#000000"),expand=True)

    def help_status(title,control=None):
        text=str(title).lower()
        if control is not None:
            if control in list(credential_inputs.values()):return "निजी credential field है। Popup में इसका मान नहीं दिखाया जाता।"
            error=getattr(control,"error_text",None)
            if error:return "इस field में validation error है: "+str(error)
            if "expiry" in text or "strike" in text or "contract" in text:return component_status("options")
            if "source" in text or "provider" in text or "symbol" in text:return component_status("market")
            return "इस नियंत्रण में अभी validation error दर्ज नहीं है। वास्तविक डेटा की स्थिति संबंधित सेक्शन में देखें।"
        if "execution capabilities" in text or "live auto trading" in text:return "Live orders: OFF • live SL/target: OFF • server automation: NOT CONNECTED"
        if "diagnostic" in text:return "इस सत्र में दर्ज errors: "+str(len(diagnostics))+"। यह पूर्ण कार्यक्षमता का प्रमाण नहीं है।"
        if "source" in text or "broker" in text:return str(connection_status.value)+" • "+component_status("market")
        if "news" in text or "headline" in text:
            data=fusion_cache.get((scan_symbol.value or "NIFTY")+":"+(scan_tf.value or "5m")) or {}
            return str(data.get("news_status","Headlines अभी उपलब्ध नहीं हैं।"))+" • "+component_status("news")
        if ("analysis" in text and "oi analysis" not in text) or "scanner" in text or "super five" in text:return str(scan_status.value)+" • "+str(scan_shared.get("basis","Analysis अभी उपलब्ध नहीं है।"))
        if "option chart" in text:return component_status("option_chart")+" • "+option_feed_status[0]
        if "chart" in text and "option" not in text:return str(tradingview_status.value)+" • "+component_status("market")
        if "alert" in text or "backtest" in text:return "यह सेवा अभी जुड़ी नहीं है।"
        if any(x in text for x in ("paper","protection","strategy","risk","target","trade")):
            return "Paper / saved-plan सुविधा है। Live orders और live automatic exit सक्रिय नहीं हैं।"
        if any(x in text for x in ("option","pcr","oi analysis","flow")):
            rows=selected_option_rows()
            if not rows:return "Verified option डेटा अभी उपलब्ध नहीं है। "+option_feed_status[0]+" • "+component_status("options")
            now=datetime.now(timezone.utc).timestamp()
            fresh=all(r.get("timestamp") is not None and 0<=now-r["timestamp"]<=90 for r in rows)
            return ("हाल के option quotes उपलब्ध हैं। " if fresh else "Option quotes पुराने हैं या समय उपलब्ध नहीं है। ")+option_feed_status[0]+" • "+component_status("options")
        sym=chain_symbol.value if current[0]==1 else (scan_symbol.value or "NIFTY")
        return quote_caption(sym)+" • स्रोत: "+str(prefs.get("source","Dhan"))+" • broker "+("जुड़ा है" if angel_feed.connected else "जुड़ा नहीं है")
    def show_help(title,control=None):
        message=describe(title,prefs.get("language","English"))
        dialog=ft.AlertDialog(title=txt("ⓘ "+str(title),17,GOLD,True),
            content=ft.Column([note(message),txt("अभी की स्थिति",14,GOLD,True),note(help_status(title,control)),note("डेटा न मिले: Refresh करें, स्रोत और expiry जाँचें। Field error हो: मान ठीक करके फिर save करें।")],tight=True,scroll=ft.ScrollMode.AUTO,width=330),
            actions=[ft.TextButton("बंद करें",on_click=lambda e:close_help(dialog))])
        localize_tree(dialog,prefs.get("language","English"))
        if hasattr(page,"open"):page.open(dialog)
        else:page.dialog=dialog;dialog.open=True;page.update()
        return dialog
    def close_help(dialog):
        if hasattr(page,"close"):page.close(dialog)
        else:dialog.open=False;page.update()
    def section(title,child):
        header=ft.Row([ft.Container(content=txt(title,13,GOLD,True),expand=True),ft.IconButton(icon=ft.Icons.INFO_OUTLINE,icon_color=MUTED,tooltip="आसान जानकारी और वर्तमान स्थिति",on_click=lambda e:show_help(title))])
        return card(header,child)
    def decorate_help(control,parent_wrap=False):
        if getattr(control,"data",None)=="help_wrapper":return control
        fields=(ft.TextField,ft.Dropdown,ft.Checkbox,ft.Switch,ft.Slider)
        if isinstance(control,fields):
            label=getattr(control,"_bk_original_label",None) or getattr(control,"label",None) or getattr(control,"tooltip",None) or "Signal agreement"
            width=getattr(control,"width",None);expand=getattr(control,"expand",None)
            if parent_wrap:
                width=min(300,max(160,float(getattr(page,"width",None) or 420)-90));expand=False
            control.expand=False
            info=ft.IconButton(icon=ft.Icons.INFO_OUTLINE,icon_size=16,icon_color=MUTED,tooltip="जानकारी",on_click=lambda e,c=control,t=label:show_help(t,c))
            if isinstance(control,(ft.Checkbox,ft.Switch)):
                # Native switch labels do not wrap on narrow Android screens.
                control._bk_external_label=True
                control._bk_original_label=label
                control.label=""
                row=ft.Row([control,ft.Container(content=txt(label,12,MUTED),expand=True),info],spacing=4)
            elif isinstance(control,ft.Slider):
                control.label="{value}%"
                control._bk_help_label=txt(f"Signal agreement: {control.value:g}%",12,MUTED)
                row=ft.Column([ft.Row([ft.Container(content=control._bk_help_label,expand=True),info]),control],horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            else:
                row=ft.Row([ft.Container(content=control,expand=True),info],spacing=4,vertical_alignment=ft.CrossAxisAlignment.CENTER)
            return ft.Column([row],data="help_wrapper",expand=expand,width=width,spacing=0,horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        if isinstance(control,(ft.Column,ft.Row)):
            control.controls=[decorate_help(c,isinstance(control,ft.Row) and bool(control.wrap)) for c in control.controls]
        elif isinstance(control,ft.Container) and control.content is not None:
            control.content=decorate_help(control.content)
        return control
    scan_shared=market_store.get("analysis",prefs.get("scanner_symbol","NIFTY"),prefs.get("scanner_timeframe","5m")) or {"direction":"WAIT","basis":"Awaiting automatic scan","tf":"—","symbol":"NIFTY"}
    if scan_shared.get("timestamp"):scan_shared["basis"]="HISTORICAL • "+age_label(scan_shared["timestamp"])+" • "+scan_shared["basis"]
    saved_ranking=market_store.get("ranking","configured51") or market_store.get("ranking","configured50") or {}
    top5_candidates=[dict(row,historical=True) for row in saved_ranking.get("rows",[]) if isinstance(row,dict) and row.get("source")==({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan"))][:5]
    top5_last_update=[saved_ranking.get("checked_at","—")]
    watch_signal_cache={r["symbol"]:r for r in saved_ranking.get("all_rows",[]) if isinstance(r,dict) and r.get("symbol") and r.get("source")==({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan"))}
    for r in top5_candidates:
        if r.get("source")==({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan")):
            watch_signal_cache.setdefault(r["symbol"],r)
    def signal_percentages(row):
        votes=row.get("votes") or []
        bulls=sum(v.get("vote")==1 for v in votes if isinstance(v,dict))
        bears=sum(v.get("vote")==-1 for v in votes if isinstance(v,dict))
        total=bulls+bears
        return (round(100*bulls/total),round(100*bears/total),total) if total else None
    def strength_widget(row, symbol=None):
        # Do not present cached Yahoo/Angel signals as Dhan watchlist signals.
        if prefs.get("source")=="Dhan" and (symbol not in tuple(["NIFTY"]+watch_symbols) or (row or {}).get("source")!="Dhan"):
            return note("Unsupported Dhan symbol" if symbol not in tuple(["NIFTY"]+watch_symbols) else "Candle analysis pending • see System Health")
        counts=signal_percentages(row or {})
        if not counts:return note("Signal agreement unavailable")
        bull,bear,total=counts
        stamp=row.get("timestamp")
        historical=row.get("historical") or not regular_hours() or not isinstance(stamp,(int,float)) or not 0<=datetime.now(timezone.utc).timestamp()-stamp<=timeframe_spec("5m")["fresh_seconds"]
        # Historical filter ratios are context, not a current directional signal.
        # Keep historical direction visible; the explicit HISTORICAL caption prevents a live claim.
        # Show directional vote proportions even for historical candles.
        # HISTORICAL / NOT live signal labels remain mandatory.
        bull_bar_color=GREEN
        bear_bar_color=RED
        bar=ft.Row([ft.Container(bgcolor=bull_bar_color,expand=bull) if bull else ft.Container(width=0),
                    ft.Container(bgcolor=bear_bar_color,expand=bear) if bear else ft.Container(width=0)],spacing=0,height=7)
        label_prefix="Historical votes (NOT live signal) • " if historical else "Filter votes • "
        label_color=GREEN
        bear_color=RED
        display_prefix="HISTORICAL • " if historical else ""
        return ft.Column([ft.Row([txt(display_prefix+"Bullish "+str(bull)+"%",11,label_color,True),txt("Bearish "+str(bear)+"%",11,bear_color,True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),bar,note(label_prefix+str(total)+" directional filters • not win probability")],spacing=2)

    def mark_ranking_historical():
        for row in top5_candidates:row["historical"]=True
    dashboard_index=["NIFTY"]
    dashboard_tool=[""]
    def dashboard_index_set(name):
        dashboard_index[0]=name
        select(0)
    def dashboard_tool_open(name):
        dashboard_tool[0]=name
        if name=="Scanner":select(3)
        elif name=="Paper Trade":select(2)
        elif name=="OI Data":select(1)
        else:select(0)
    def open_candidate_chart(symbol):
        scan_symbol.value=symbol
        select(3)
        trigger_scan()
    page_save_status=[ft.Text("",size=12,color=MUTED) for _ in range(4)]
    def risk_overview():
        ledger=paper_risk_ledger()
        return section("TODAY'S PAPER RISK",ft.Column([
            note("Entries: "+str(ledger["entries"])+" / "+str(prefs.get("max_trades",2))),
            note("Remaining planned-risk budget: INR "+format(max(0,float(prefs.get("max_daily_loss",1000))-float(ledger["planned_risk_used"])),",.2f")),
            note("Emergency stop: "+("ON" if prefs.get("emergency_stop") else "OFF")),
            note("Protection: "+prefs.get("protection_mode","Manual")+" • paper demonstration only; live monitoring disconnected")
        ],spacing=4))
    def component_status(kind,sym=None,interval=None):
        sym=sym or (scan_symbol.value or "NIFTY");interval=interval or (scan_tf.value or "5m")
        if kind=="market":key="market:"+prefs.get("source","Dhan")+":"+sym+":"+interval
        elif kind=="options":key="options:"+chain_symbol.value+":"+str(expiry.value)
        elif kind=="option_chart":key="option_chart:"+chain_symbol.value+":"+str(expiry.value)+":"+str(option_strike.value)+":"+str(option_side.value)
        else:key="news:"+sym
        row=health.get(key)
        if not row:
            if kind=="market" and quotes.get(sym):return "Saved snapshot • "+quote_caption(sym)+" • no new request recorded in this session"
            if kind in ("options","option_chart") and selected_option_rows():return "Saved option snapshot • not proof of a live connection • no new request recorded in this session"
            return "No request recorded for this selection yet"
        def stamp(value):
            return datetime.fromtimestamp(value,timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M:%S IST") if isinstance(value,(int,float)) else "Unavailable"
        return row.get("state","Unknown")+" • source: "+row.get("source","")+" • data time: "+stamp(row.get("data_time"))+" • last attempt: "+stamp(row.get("last_attempt"))+" • last success: "+stamp(row.get("last_success"))+" • "+row.get("error","")
    async def retry_selected_data():
        broker_retry[0]=0;broker_failures[0]=0
        await refresh_selected_options()
        if not scan_busy[0]:await scan_market()
        if current[0] in (0,1,3):select(current[0])
    def data_overview():
        # Compact error-first diagnostics; never display secrets.
        dhan=prefs.get("source")=="Dhan"
        connected=dhan_feed.connected if dhan else angel_feed.connected if prefs.get("source")=="Broker API" else False
        yahoo=prefs.get("source")=="Yahoo Finance"
        if yahoo:
            connected=any(row.get("source")=="Yahoo Finance" and isinstance(row.get("price"),(int,float)) for row in quotes.values())
        total=int(scan_progress.get("total",0) or 0)
        valid=int(scan_progress.get("valid",0) or 0)
        state=str(scan_progress.get("state","Waiting"))
        problems=[]
        if dhan and dhan_batch_issue[0]:
            problems.append("Dhan watchlist batch: "+dhan_batch_issue[0])
        # Individual index/stock retries can fail even when the 51-equity scan
        # completed. Keep their failures visible until that symbol succeeds.
        if connected and failed_symbols:
            for failed,reason in list(failed_symbols.items())[:3]:
                problems.append("Market data "+str(failed)+": "+str(reason)[:100])
        if not connected:problems.append("Yahoo quote not verified" if yahoo else "Provider disconnected; reconnect in Settings")
        # A disconnected Dhan session is one root cause, not four independent
        # failures. Preserve the detailed diagnostics but avoid alarming users
        # with derivative scan/quote/chart errors until re-authentication.
        if dhan and connected and "FeedError" in component_status("market"):
            problems.append("Chart data request failed; scanner completion does not verify chart")
        market_health=component_status("market")
        if connected and ("STALE" in market_health or "UNAVAILABLE" in market_health):
            problems.append("Chart warning: historical or unavailable data; not verified live")
        # HISTORICAL is a successful candle fetch, not a live-price verification.
        # Keep that limitation visible in the detailed chart status without
        # counting it as a broken chart or an active error.
        if yahoo and ("awaiting" in state.lower() or valid==0):
            problems.append("Yahoo scanner analysis pending; historical quotes are not live")
        # Feature availability is distinct from feed readiness. Never label a
        # visible control LIVE merely because its page can open.
        feature_rows=[
            ("Dashboard", "ENABLED", "health and navigation"),
            ("Watchlist", "ENABLED" if connected else "DEGRADED", "quotes require verified provider and freshness"),
            ("Charts", "DEGRADED" if ("UNAVAILABLE" in market_health or "STALE" in market_health or not connected) else "ENABLED", market_health[:95]),
            ("Scanner", "DEGRADED" if not connected or valid==0 else "HISTORICAL",
             str(valid)+"/"+str(total)+" candle analyses; live signal not verified"),
            ("Super Five", "DEGRADED" if not connected or valid==0 else "HISTORICAL",
             "saved candle candidates; live ranking not verified"),
            ("Settings", "ENABLED", "provider selection and preferences"),
            ("Paper trading", "ENABLED", "simulation only; no broker orders"),
            ("Real BUY / SELL", "DISABLED", "live order execution intentionally unavailable"),
            ("News analysis", "EXPERIMENTAL", "RSS phrase cues, not verified trading signals"),
            ("Dhan token auto-renewal", "NOT VERIFIED", "Oracle timer activation cannot be checked from this app"),
            ("Server health", "NOT VERIFIED", "configured URL does not prove server availability"),
        ]
        feature_details=[note("FEATURE STATUS • enabled means UI available, not verified live feed")]
        feature_details.extend(note(label+": "+status+" • "+reason) for label,status,reason in feature_rows)
        doctor_items=[diagnose(problem) for problem in problems[:3]]
        details=[
            note("ERROR DOCTOR • rule-based local diagnosis; no remote AI or secret upload"),
            *[note(code+" • "+cause+" • "+action) for code,cause,action in doctor_items],
            note("Provider: "+prefs.get("source","Unknown")+" • "+(("quote available; freshness unverified" if yahoo else "session active (quote freshness unverified)") if connected else ("quote not verified" if yahoo else "disconnected; reconnect required"))),
            note("Watchlist: "+str(sum(1 for symbol in watch_symbols if (quotes.get(symbol) or {}).get("source")=="Dhan" and isinstance((quotes.get(symbol) or {}).get("price"),(int,float))))+"/"+str(len(watch_symbols))+" saved/displayed LTP • quote time unverified"+(" • DISCONNECTED; cached prices are not live" if not connected else "") if dhan else "Watchlist: check selected feed"),
            note("Candle scan: "+str(valid)+"/"+str(total)+" • "+state[:100] if dhan else "Candle scan: awaiting "+prefs.get("source","selected")+" analysis"),
            note("Chart: "+component_status("market")),
            note("Super Five: historical analysis only until latest completed candle is verified"),
            note("Server: "+("HTTPS configured" if prefs.get("api_url") else "HTTPS not configured")+" • remote health not independently verified"),
            note("Settings: "+preference_writer.status+" • disk "+("saved" if preference_writer.disk_saved else "not confirmed")),
            note("UI version: "+APP_VERSION+" • verify APK package version"),
            note(session_caption()),
            note("Live orders OFF • historical data is not a live signal"),
            note("Cache: "+market_store.status),
            note("News: public RSS headlines; experimental phrase cues"),
            note("Latest feed: "+market_status[:130]),
            *feature_details
        ]
        return section("SYSTEM HEALTH",ft.Column([
            ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED if problems else ft.Icons.CHECK_CIRCLE_OUTLINE,color=RED if problems else GREEN,size=17),ft.Container(content=txt(str(len(problems))+" issue(s) need attention" if problems else "No active errors reported",11,RED if problems else GREEN,True),expand=True),txt(prefs.get("source",""),10,MUTED)],spacing=5),
            *[txt(item,11,RED) for item in problems[:3]],
            ft.ExpansionTile(title=note("Full diagnostics • "+str(total)+" scan targets"),initially_expanded=False,controls=details),
            ft.TextButton("Retry data",on_click=lambda e:page.run_task(retry_selected_data))
        ],spacing=2))
    def news_event_overview():
        data=fusion_cache.get((scan_symbol.value or "NIFTY")+":"+(scan_tf.value or "5m")) or {}
        rows=[note("Company/global headlines are context; earnings and exchange calendar are not connected.")]
        for item in (data.get("headlines",[])+data.get("global_headlines",[]))[:3]:
            rows.append(ft.TextButton(content=ft.Text(item["source"]+" • "+item["title"],size=12,color=WHITE),on_click=lambda e,url=item["url"]:page.launch_url(url)))
        if len(rows)==1:rows.append(note("No news loaded for the selected symbol yet. Open Scanner and refresh."))
        return section("NEWS & EVENT CONTEXT",ft.Column(rows,spacing=4))
    def display_analysis(sym,data):
        raw=data.get("bars") or []
        live=analyze_current(raw,filter_selected[:],"5m")
        display=dict(live)
        completed=[bar for bar in raw if bar[0]+300<=datetime.now(timezone.utc).timestamp()]
        quality={"usable":False,"bars":[]}
        if completed:
            quality=quality_check(completed,300,now=completed[-1][0]+300)
            if quality["usable"]:
                selected=[name for name in filter_selected if filter_modes.get(name,"Analysis")!="Chart"]
                display=analyze(quality["bars"],selected,"5m")
                if display.get("score",0)<float(prefs.get("confidence",75)):display.update(bias="WAIT",score=0)
        if not completed or not quality["usable"]:
            display.update(bias="DATA UNAVAILABLE",score=0,timestamp=None,reason="Insufficient or invalid completed candles; last valid result retained")
        if data.get("source")=="Dhan" and (dhan_feed.historical_only or data.get("freshness")=="historical_unverified"):
            display.update(bias="WAIT",score=0,
                           reason=str(display.get("reason",""))+" • Dhan historical-only; live LTP not verified")
        age=datetime.now(timezone.utc).timestamp()-(display.get("timestamp") or 0)
        # Quote freshness is not established by a recent historical candle.
        provider_unverified = (data.get("source") == "Dhan" and
                               (data.get("freshness") not in ("verified_live", "live_verified") or data.get("live_verified") is not True))
        display.update(symbol=sym,source=data.get("source","Unavailable"),
                       freshness=data.get("freshness","unverified"),
                       live_verified=data.get("live_verified") is True,
                       historical=bool(data.get("cached")) or provider_unverified or
                       (data.get("source")=="Dhan" and dhan_feed.historical_only) or
                       not 0<=age<=timeframe_spec("5m")["fresh_seconds"],age=max(0,int(age)))
        return display
    def historical_vote_agreement(data):
        """Completed 5m candle votes only; never promote historical to live."""
        raw=data.get("bars") or []
        if data.get("source")!="Dhan" or not isinstance(raw,list):
            return None
        now=datetime.now(timezone.utc).timestamp()
        completed=[bar for bar in raw if isinstance(bar,(list,tuple)) and len(bar)>=5
                   and isinstance(bar[0],(int,float)) and bar[0]+300<=now]
        if not completed:
            return None
        quality=quality_check(completed,300,now=completed[-1][0]+300)
        if not quality.get("usable"):
            return None
        selected=[name for name in filter_selected if filter_modes.get(name,"Analysis")!="Chart"]
        result=analyze(quality["bars"],selected,"5m")
        votes=[v.get("vote") for v in result.get("votes",[]) if isinstance(v,dict)]
        bulls=votes.count(1)
        bears=votes.count(-1)
        total=bulls+bears
        if not total:
            return None
        return (round(100*bulls/total),round(100*bears/total),total)

    def historical_vote_bar(agreement):
        if agreement is None:
            return note("5m historical candle votes unavailable • data quality pending")
        bull,bear,count=agreement
        return ft.Column([
            ft.Row([txt("Bullish "+str(bull)+"%",11,GREEN,True),
                    txt("Bearish "+str(bear)+"%",11,RED,True)],wrap=True,spacing=10),
            ft.Row([ft.Container(bgcolor=GREEN,height=7,expand=max(1,bull)),
                    ft.Container(bgcolor=RED,height=7,expand=max(1,bear))],spacing=0),
            note("Historical 5m votes • "+str(count)+" filters • NOT live")
        ],spacing=3)

    def publish_partial_ranking(results):
        expected_source={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
        available=[dict(res,symbol=sym) for sym,res in results.items()
                   if res and res.get("timestamp") and res.get("source")==expected_source]
        available.sort(key=lambda r:(not r.get("historical"),r["bias"] in ("BULLISH","BEARISH"),r.get("score",0),r.get("timestamp",0)),reverse=True)
        if prefs.get("source")=="Dhan":
            # Do not surface unverified historical bullish/bearish calls as live picks.
            previous=[row for row in top5_candidates if row.get("source")=="Dhan"]
            chosen=[dict(row,bias="WAIT",score=0,
                         reason=str(row.get("reason",""))+" • Historical/unverified; no live signal")
                    if row.get("historical") else row for row in available[:5]]
            used={row.get("symbol") for row in chosen}
            for row in previous+saved_ranking.get("rows",[]):
                if len(chosen)>=5:break
                if row.get("source")!="Dhan" or not row.get("symbol") or row["symbol"] in used:continue
                chosen.append(dict(row,bias="WAIT",score=0,historical=True,
                                   reason="Last saved Dhan ranking • Historical/unverified; no live signal"))
                used.add(row["symbol"])
            top5_candidates[:]=chosen
            return available
        previous=top5_candidates[:]
        if available:top5_candidates[:]=available[:5]
        used={row["symbol"] for row in top5_candidates}
        for row in previous+saved_ranking.get("rows",[]):
            if row.get("source")!=({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan")):continue
            if len(top5_candidates)>=5:break
            if row["symbol"] not in used:top5_candidates.append(dict(row,historical=True));used.add(row["symbol"])
        for sym in watch_symbols:
            if len(top5_candidates)>=5:break
            if sym not in used:top5_candidates.append({"symbol":sym,"bias":"DATA UNAVAILABLE","score":0,"timestamp":None,"age":0,"reason":"No valid candle data","historical":True});used.add(sym)
        return available
    async def super_five_minute_refresh():
        # Re-rank cached, completed 5m candles every 15 seconds (local only).
        # Never issue another 51-symbol historical API burst from this task.
        while True:
            await asyncio.sleep(15)
            try:
                if not app_active[0] or (prefs.get("source")=="Dhan" and not dhan_feed.connected):
                    continue
                generation=provider_generation[0]
                expected_source={"Dhan":"Dhan","Broker API":"Angel One",
                                 "Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
                if not expected_source:
                    continue
                results={}
                for sym in watch_symbols:
                    snapshot=quotes.get(sym) or {}
                    if snapshot.get("source")!=expected_source or not snapshot.get("bars"):
                        continue
                    result=display_analysis(sym,snapshot)
                    if result.get("timestamp"):
                        results[sym]=result
                if generation!=provider_generation[0] or not results:
                    continue
                publish_partial_ranking(results)
                if current[0]==0:
                    request_view_refresh(0)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log_error("super_five_minute_refresh",exc)
                if current[0]==0:
                    request_view_refresh(0)
    def super_five_card():
        # A disconnected broker must never display restored directional rankings
        # as actionable Super Five candidates, even when snapshots survived restore.
        if prefs.get("source")=="Dhan" and not dhan_feed.connected:
            return section("SUPER FIVE • CONNECTION REQUIRED",ft.Column([
                note("Dhan disconnected • connect and verify the feed in Settings before scanning."),
                note("Saved historical rankings are hidden while disconnected; no live signal is available."),
                note("Historical analysis unavailable • Dhan reconnect required")
            ],spacing=7))
        rows=top5_candidates[:]
        if not rows:
            rows=[{"symbol":sym,"bias":"DATA UNAVAILABLE","reason":"No saved analysis; waiting for first successful fetch","timestamp":None} for sym in watch_symbols[:5]]
        controls=[note(("Dhan: 51 verified equity mappings • freshness unverified" if prefs.get("source")=="Dhan" else "Configured 51-company watchlist") +" • last completed-candle analysis • not a trade order"),
            note("Historical analysis: "+str(scan_progress["state"])+" • separate from watchlist quote refresh")]
        # Keep Super Five focused on five candidates, not a scrolling wall
        # of up to 51 provider errors and retry buttons. Full per-symbol
        # diagnostics remain in System Health / Scanner.
        if failed_symbols:
            controls.append(note(str(len(failed_symbols))+
                " candle histories unavailable • details in System Health / Scanner"))

        now=datetime.now(timezone.utc).timestamp()
        for row in rows:
            stamp=row.get("timestamp");age=now-stamp if isinstance(stamp,(int,float)) else None
            expected_source={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            historical=(row.get("historical") or row.get("cached") or row.get("source")!=expected_source or
                        (prefs.get("source")=="Dhan" and (row.get("freshness") not in ("verified_live","live_verified") or row.get("live_verified") is not True)) or
                        age is None or not 0<=age<=timeframe_spec("5m")["fresh_seconds"] or not regular_hours())
            status="HISTORICAL / last available" if historical else "Recent analysis"
            when=datetime.fromtimestamp(stamp,timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %Y %H:%M IST") if stamp else "Time unavailable"
            color=GREEN if row["bias"]=="BULLISH" else RED if row["bias"]=="BEARISH" else MUTED
            # Rendering is the final safety gate: a restored ranking can predate
            # the current provider verification or market session.
            direction=("NO LIVE SIGNAL" if prefs.get("source")=="Dhan" and historical
                       else "HISTORICAL "+row["bias"] if historical and row["bias"] in ("BULLISH","BEARISH")
                       else "NO CLEAR SIGNAL" if row["bias"]=="WAIT" else row["bias"])
            controls.append(ft.Container(content=ft.Column([txt(row["symbol"]+" • "+direction,14,color,True),note(status+" • "+age_label(stamp)+" • "+when),note("Source: "+row.get("source","Unavailable")),note("LTP: "+quote_price(row["symbol"])+" • quote time unverified" if prefs.get("source")=="Dhan" else "LTP: "+quote_price(row["symbol"])),note(row.get("reason","")),strength_widget(row,row.get("symbol"))],spacing=3),bgcolor=PANEL2,padding=8,border_radius=8,on_click=lambda e,sym=row["symbol"]:open_candidate_chart(sym)))
        controls.append(note("Historical conclusions are kept for reference. Freshness checks still gate new live signals."))
        return section("SUPER FIVE • LAST AVAILABLE ANALYSIS",ft.Column(controls,spacing=7))
    async def retry_failed_symbol(symbol):
        generation=provider_generation[0]
        try:
            data=await asyncio.to_thread(get_market_data,symbol,"5m","5d")
            if generation!=provider_generation[0]:return
            result=display_analysis(symbol,data)
            if not result.get("timestamp"):raise ValueError("No completed candle analysis")
            quotes[symbol]=data;failed_symbols.pop(symbol,None)
            existing={r["symbol"]:r for r in top5_candidates if r.get("timestamp")}
            existing[symbol]=result;publish_partial_ranking(existing)
            market_store.put("ranking",("configured51",),{"rows":top5_candidates,"checked_at":datetime.now().strftime("%d %b %H:%M")})
        except Exception as exc:failed_symbols[symbol]=safe_error(exc)
        if current[0]==0:request_view_refresh(0)
    def dashboard_index_analysis():
        panels=[]
        # Three independent persisted slots; restrict selections to the verified
        # blue-chip universe plus supported/requested indexes.
        choices=list(dict.fromkeys(["NIFTY","BANKNIFTY","SENSEX"]+watch_symbols))
        defaults=("NIFTY","RELIANCE","HDFCBANK")
        for slot in range(3):
            key="dashboard_analysis_slot_"+str(slot+1)
            sym=prefs.get(key,defaults[slot])
            if sym not in choices:
                sym=defaults[slot]
            def select_slot(e,setting=key):
                selected=e.control.value
                if selected not in choices:
                    return
                prefs[setting]=selected
                save()
                request_view_refresh(0)
            picker=ft.Dropdown(
                label="Analysis "+str(slot+1)+" • select stock / index",
                value=sym,
                options=[ft.dropdown.Option(x) for x in choices],
                on_change=select_slot,
                dense=True,
                expand=True,
            )
            snapshot=quotes.get(sym) or {}
            source=snapshot.get("source")
            valid_source=source=={"Dhan":"Dhan","Broker API":"Angel One",
                                  "Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            # Index prices are not part of the 51-equity Dhan snapshot.
            # Never suggest a missing index quote is a successfully refreshed LTP.
            if prefs.get("source")=="Dhan" and sym in ("NIFTY","BANKNIFTY","SENSEX") and (not valid_source or not isinstance(snapshot.get("price"),(int,float))
                    or isinstance(snapshot.get("price"),bool) or not math.isfinite(snapshot["price"])
                    or snapshot["price"]<=0):
                rows_note=("Index Dhan LTP unavailable • no verified quote returned for this index • "
                           "51-equity snapshot does not include indexes")
            else:
                rows_note=None
            rows=[picker,ft.Row([txt(sym,13,GOLD,True),
                          ft.Container(content=txt(quote_price(sym),15,GOLD,True),expand=True),
                          txt(quote_change(sym),11,price_color(sym),True)],spacing=8)]
            if prefs.get("source")=="Dhan" and sym in ("NIFTY","BANKNIFTY","SENSEX") and snapshot.get("provider_status")=="provider_data_unavailable":
                rows.append(note("Dhan index provider data unavailable • displayed price is LAST KNOWN, not a fresh live quote"))
            elif rows_note:
                rows.append(note(rows_note))
            # Reuse an already-loaded 5m candle series, never an index LTP
            # snapshot (which contains no historical bars). Do not issue a
            # network request while building the dashboard.
            candle_data=(chart_snapshots.get((sym,"5m",provider_generation[0])) or
                candles.get("scanner_chart_"+sym) or
                (snapshot if snapshot.get("bars") else {}))
            candle_tf=candle_data.get("_scanner_timeframe","5m")
            if candle_tf!="5m" or candle_data.get("source")!=source:
                candle_data={}
            quote_stamp=snapshot.get("fetched_at")
            if (valid_source and isinstance(quote_stamp,(int,float))
                    and not isinstance(quote_stamp,bool) and math.isfinite(quote_stamp)):
                rows.append(note("LTP last collected • "+age_label(quote_stamp)+
                                 " • exchange timestamp unverified"))
            else:
                rows.append(note("LTP update unavailable • last known value only"))
            if not valid_source or not candle_data.get("bars"):
                rows.append(note("Candle bias: UNAVAILABLE • no verified 5m candle series • open 5m Scanner chart to load candles"))
            else:
                try:
                    rows.append(historical_vote_bar(historical_vote_agreement(candle_data)))
                    analysis=display_analysis(sym,candle_data)
                    if not analysis.get("timestamp"):
                        rows.append(note("Candle signal: UNAVAILABLE • insufficient completed candles"))
                    else:
                        historical=analysis.get("historical",True)
                        rows.append(note(("HISTORICAL • " if historical else "5m • ")+
                                         str(analysis.get("bias","WAIT"))+
                                         " • "+age_label(analysis["timestamp"])))
                        if historical:
                            rows.append(note("Previous candle direction is not a current signal"))
                except Exception as exc:
                    log_error("dashboard_index_analysis_"+sym,exc)
                    rows.append(note("Candle analysis unavailable • see diagnostics"))
            panels.append(ft.Container(content=ft.Column(rows,spacing=3),
                                       bgcolor=PANEL2,border_radius=10,padding=10))
        return section("INDEX ANALYSIS • AUTO STATUS",ft.Column(panels,spacing=8))
    def dashboard():
        # Keep one canonical three-slot index analysis panel. Duplicate market
        # overview, error-monitor and news cards cluttered the Home screen and
        # made ordinary card taps look like an implicit refresh action.
        # Diagnostics and news data remain available in their dedicated views.
        return [
            data_overview(),
            dashboard_index_analysis(),
            note('Viewing: ' + (scan_symbol.value or 'NIFTY') + ' • ' + (scan_tf.value or '5m')),
            fusion_card(scan_shared['symbol'], scan_shared['tf'] if scan_shared['tf'] != '—' else '5m', compact=True),
            section('CANDLE ANALYSIS • ' + scan_shared['direction'],
                    ft.Column([note(scan_shared['symbol'] + ' • ' + scan_shared['tf'] + ' candles'),
                               note(scan_shared['basis'])], spacing=4)),
            dashboard_positions(),
            section('OPTIONS DATA • '+str(chain_symbol.value),
                    ft.Column([note(option_feed_status[0]), option_metrics('OI')])),
            super_five_card(),
            risk_overview(),
        ]

    search=ft.TextField(label="Search in selected list",hint_text="e.g. RELIANCE",expand=True,border_color=BORDER,color=WHITE,bgcolor=PANEL2)
    watch_symbols=["RELIANCE","HDFCBANK","ICICIBANK","TCS","INFY","BHARTIARTL","SBIN","ITC","LT","AXISBANK","KOTAKBANK","HINDUNILVR","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","TITAN","SUNPHARMA","ULTRACEMCO","ASIANPAINT","NTPC","POWERGRID","TMPV","TMCV","TATASTEEL","JSWSTEEL","HCLTECH","WIPRO","TECHM","NESTLEIND","HINDALCO","ONGC","COALINDIA","ADANIENT","ADANIPORTS","BEL","TRENT","EICHERMOT","GRASIM","CIPLA","DRREDDY","APOLLOHOSP","DIVISLAB","SBILIFE","HDFCLIFE","BAJAJ-AUTO","HEROMOTOCO","BRITANNIA","INDUSINDBK","SHRIRAMFIN","BPCL"]
    watch_groups=[list(prefs.get("watchlist_"+str(i),watch_symbols if i==1 else [])) for i in range(1,6)]
    # Preserve existing user lists while migrating the old Tata Motors symbol.
    watch_migrated=False
    for group in watch_groups:
        if "TATAMOTORS" in group:
            expanded=[]
            for item in group:
                expanded.extend(["TMPV","TMCV"] if item=="TATAMOTORS" else [item])
            group[:]=list(dict.fromkeys(expanded))
            watch_migrated=True
    if watch_migrated:
        for i,group in enumerate(watch_groups,1):
            prefs["watchlist_"+str(i)]=list(group)
        save()
    active_watch=[0]
    watch_list=ft.Column(spacing=8,scroll=ft.ScrollMode.AUTO)
    selected_watch=[""]
    watch_filter=["All"]
    add_symbol=ft.TextField(label="Add NSE symbol",hint_text="e.g. HDFCBANK",expand=True)
    feedback=txt("",12,MUTED)
    def store_watch():
        for i,group in enumerate(watch_groups,1):prefs["watchlist_"+str(i)]=list(group)
        return save()
    def all_watch_symbols():
        return list(dict.fromkeys(sym for group in watch_groups for sym in group))
    def selection_symbols():
        return list(dict.fromkeys(["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"]+watch_symbols+all_watch_symbols()+list(prefs.get("custom_symbols",[]))))
    def sync_symbol_choices():
        symbols=selection_symbols()
        for picker in (chain_symbol,scan_symbol,bot_symbol,symbol):
            values=list(dict.fromkeys(symbols+([picker.value] if picker.value else [])+(["Custom"] if picker is bot_symbol else [])))
            picker.options=[ft.dropdown.Option(x) for x in values]
    def symbol_search(picker):
        field=ft.TextField(label="Find stock / index",hint_text="TCS, HDFCBANK, NIFTY…",dense=True)
        def search_symbols(e):
            query=(field.value or "").strip().upper()
            values=selection_symbols()+(["Custom"] if picker is bot_symbol else [])
            picker.options=[ft.dropdown.Option(x) for x in dict.fromkeys(values+([picker.value] if picker.value else [])) if not query or query in x or x==picker.value]
            page.update()
        field.on_change=search_symbols
        return field
    def change_watch(i):
        active_watch[0]=i
        watch_filter[0]="All"
        search.value=""
        feedback.value=""
        select(4)
    async def validate_and_add(sym, target_list):
        # Preserve the chosen list across asynchronous provider requests.
        # Known NSE blue chips can be saved even when market data is unavailable.
        if sym not in watch_symbols:
            try:
                q=await asyncio.to_thread(get_market_data,sym)
                if q.get("price") is None:raise ValueError("No market price")
                quotes[sym]=q
            except Exception:
                feedback.value="Symbol not verified. Check ticker or provider; not added."
                page.update()
                return
        if sym not in watch_groups[target_list]:
            if len(watch_groups[target_list])>=50:
                if active_watch[0]==target_list:
                    feedback.value="List is full (50 symbols maximum). Remove a symbol first."
                    page.update()
                return
            watch_groups[target_list].append(sym)
            store_watch()
        sync_symbol_choices()
        if sym not in [o.key for o in chain_symbol.options]:
            chain_symbol.options.append(ft.dropdown.Option(sym))
        if active_watch[0]==target_list:
            feedback.value=sym+" added and saved to List "+str(target_list+1)
            if (add_symbol.value or "").strip().upper().removesuffix(".NS")==sym:
                add_symbol.value=""
            select(4)
        else:
            # Never jump away from the list the user selected while validation ran.
            page.update()
    def add_watch(e):
        sym=(add_symbol.value or "").strip().upper().removesuffix(".NS")
        target_list=active_watch[0]
        if not sym or len(sym)>25 or not all(c.isalnum() or c in "-&." for c in sym):
            feedback.value="Enter a valid NSE ticker (letters, numbers, -, &, .)."
        elif sym in watch_groups[target_list]:
            feedback.value="Already in this list."
        elif len(watch_groups[target_list])>=50:
            feedback.value="List is full (50 symbols maximum). Remove a symbol first."
        else:
            feedback.value="Saving known NSE symbol..." if sym in watch_symbols else "Checking market symbol..."
            page.run_task(validate_and_add,sym,target_list)
        page.update()
    def set_filter(v):
        watch_filter[0]=v
        select(4)
    def open_stock(sym):
        selected_watch[0]=sym
        if sym not in [o.key for o in symbol.options]:
            symbol.options.append(ft.dropdown.Option(sym))
        symbol.value=sym
        chart_tab[0]="Chart"
        # Avoid a second request when render_page already schedules chart loading.
        if current[0]==5:
            page.run_task(load_chart)
        else:
            select(5)
    def remove_stock(sym):
        group=watch_groups[active_watch[0]]
        if sym in group:
            group.remove(sym)
            store_watch()
            feedback.value=sym+" removed from List "+str(active_watch[0]+1)
        select(4)
    def fill_watch(_=None):
        watch_list.controls.clear()
        visible_count=0
        for sym in watch_groups[active_watch[0]]:
            if search.value and search.value.upper() not in sym:continue
            quote_row=quotes.get(sym) or {}
            quote_source=quote_row.get("source")
            expected_quote_source={"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan")
            change=quote_row.get("change") if not dhan_offline() and quote_source==expected_quote_source else None
            # Price movement and candle-filter agreement are different signals.
            valid_change=(quote_source==expected_quote_source and not dhan_offline()
                          and isinstance(change,(int,float)) and not isinstance(change,bool)
                          and math.isfinite(change))
            direction="Bullish" if valid_change and change>0 else "Bearish" if valid_change and change<0 else "Neutral" if valid_change else "Unavailable"
            quote_age=time.time()-quote_row.get("fetched_at",0) if isinstance(quote_row.get("fetched_at"),(int,float)) else None
            quote_fresh=(quote_source==expected_quote_source and quote_age is not None and 0<=quote_age<=60
                         and isinstance(quote_row.get("price"),(int,float)) and not isinstance(quote_row["price"],bool)
                          and math.isfinite(quote_row["price"]) and quote_row["price"]>0
                         and not dhan_offline())
            quote_label=("Cached Dhan LTP • refresh failed • exchange time unverified"
                         if prefs.get("source")=="Dhan" and watch_batch_status[0].startswith("Dhan batch failed:") else
                         ("Recent Dhan LTP • exchange time unverified" if prefs.get("source")=="Dhan" else
                          "Recent quote • exchange time unverified") if quote_fresh else "Cached/unverified quote")
            signal_row=watch_signal_cache.get(sym,{})
            signal_counts=signal_percentages(signal_row)
            signal_stamp=signal_row.get("timestamp")
            signal_fresh=(signal_row.get("source")==({"Broker API":"Angel One","Dhan":"Dhan","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan"))
                          and not signal_row.get("historical") and regular_hours()
                          and isinstance(signal_stamp,(int,float)) and not isinstance(signal_stamp,bool)
                          and math.isfinite(signal_stamp) and signal_stamp>0
                          and 0<=datetime.now(timezone.utc).timestamp()-signal_stamp<=timeframe_spec("5m")["fresh_seconds"])
            signal_available=(signal_row.get("source")==expected_quote_source and
                              isinstance(signal_stamp,(int,float)) and not isinstance(signal_stamp,bool)
                              and math.isfinite(signal_stamp) and signal_stamp>0 and signal_counts is not None)
            signal_direction=("Bullish" if signal_counts[0]>signal_counts[1] else
                              "Bearish" if signal_counts[1]>signal_counts[0] else "Neutral") if signal_available else "Neutral"
            if watch_filter[0]!="All" and watch_filter[0]!=signal_direction:continue
            visible_count+=1
            watch_list.controls.append(ft.Row([
                ft.Container(content=ft.Row([ft.Icon(ft.Icons.CANDLESTICK_CHART,color=GOLD,size=20),ft.Column([txt(sym,12,WHITE,True),note(("Price "+direction+" • provider change" if valid_change else "Price change unavailable • reference unverified")),note("Candle: "+(signal_direction if signal_fresh else "Historical • not live")),note(quote_label),strength_widget(signal_row,sym)],expand=True,spacing=3),ft.Column([txt(quote_price(sym) if quote_source==expected_quote_source else "—",13,price_color(sym) if quote_source==expected_quote_source else MUTED,True),txt("CONNECT DHAN" if dhan_offline() else quote_change(sym) if quote_source==expected_quote_source else "SOURCE MISMATCH",10,price_color(sym) if quote_source==expected_quote_source else MUTED)],horizontal_alignment=ft.CrossAxisAlignment.END)],spacing=8),bgcolor=PANEL,border_radius=9,padding=6,expand=True,on_click=lambda e,v=sym:open_stock(v)),
                ft.IconButton(icon=ft.Icons.CLOSE,icon_color=RED,tooltip="Remove from this list",on_click=lambda e,v=sym:remove_stock(v))
            ],spacing=2))
        if visible_count==0:
            message="No matching stocks found. Clear search to show this list." if search.value or watch_filter[0]!="All" else "This watchlist is empty. Add a stock below."
            watch_list.controls.append(note(message))
        page.update()
    search.on_change=fill_watch
    def clear_watch_search(e):
        search.value=""
        fill_watch()
    watch_batch_busy=[False]
    watch_batch_status=["Dhan batch not checked on this screen"]
    watch_batch_last_attempt=[0.0]
    watch_batch_last_success=[0.0]
    async def refresh_watch_batch():
        nonlocal market_status
        if watch_batch_busy[0] or prefs.get("source")!="Dhan":
            return
        if not dhan_feed.connected:
            watch_batch_status[0]="Dhan reconnect required in Settings"
            request_view_refresh(4)
            return
        watch_batch_busy[0]=True
        watch_batch_last_attempt[0]=time.monotonic()
        generation=provider_generation[0]
        watch_batch_status[0]="Fetching Dhan equity LTP..."
        request_view_refresh(4)
        try:
            batch=await asyncio.to_thread(dhan_feed.batch_quotes)
            if not batch:
                raise FeedError("Empty Dhan batch response")
            if generation!=provider_generation[0] or prefs.get("source")!="Dhan":
                return
            with dhan_batch_lock:
                dhan_batch_cache.update(generation=generation,updated=time.monotonic(),quotes=batch)
            # Preserve missing symbols' last valid Dhan quotes as historical/unverified.
            # Partial status below must not imply a complete live refresh.
            for ticker,snapshot in batch.items():
                if ticker in all_watch_symbols() and snapshot.get("source")=="Dhan" and isinstance(snapshot.get("price"),(int,float)) and not isinstance(snapshot.get("price"),bool) and math.isfinite(snapshot["price"]) and snapshot["price"]>0:
                    old=quotes.get(ticker) or {}
                    quotes[ticker]=dict(snapshot,change=None,
                        bars=old.get("bars",[]) if old.get("source")=="Dhan" else [],
                        fetched_at=time.time())
            # Missing symbols retain their last Dhan price, but must not retain
            # a previously verified-live freshness label after a partial poll.
            for ticker in all_watch_symbols():
                snapshot=batch.get(ticker)
                valid=(isinstance(snapshot,dict) and snapshot.get("source")=="Dhan"
                       and isinstance(snapshot.get("price"),(int,float))
                       and not isinstance(snapshot.get("price"),bool)
                       and math.isfinite(snapshot["price"]) and snapshot["price"]>0)
                if not valid and (old:=quotes.get(ticker)) and old.get("source")=="Dhan":
                    quotes[ticker]=dict(old,freshness="unverified",live_verified=False)
            total_symbols=len(all_watch_symbols())
            # A partial batch is not a complete refresh even if older quotes remain cached.
            received=sum(1 for ticker in all_watch_symbols() if
                         (snapshot:=batch.get(ticker)) and snapshot.get("source")=="Dhan"
                         and isinstance(snapshot.get("price"),(int,float))
                         and not isinstance(snapshot.get("price"),bool)
                         and math.isfinite(snapshot["price"]) and snapshot["price"]>0)
            dhan_batch_issue[0]=(f"Partial Dhan batch: {received}/{total_symbols} valid prices returned"
                                 if received<total_symbols else None)
            if dhan_feed.connected:
                connection_status.value=(f"Dhan connected • {received}/{total_symbols} valid equity LTP prices returned • "
                                         "timestamps unverified")
                connection_status.color=GOLD if dhan_batch_issue[0] else GREEN
            # Snapshot age is the Oracle collection age, not an exchange timestamp.
            snapshot_ages=[item.get("snapshot_age_seconds") for item in batch.values()
                           if isinstance(item,dict) and isinstance(item.get("snapshot_age_seconds"),(int,float))
                           and not isinstance(item.get("snapshot_age_seconds"),bool)
                           and math.isfinite(item["snapshot_age_seconds"]) and item["snapshot_age_seconds"]>=0]
            snapshot_age_label=(f"Oracle snapshot age {max(snapshot_ages):.0f}s • "
                                if snapshot_ages else "Oracle snapshot age unknown • ")
            watch_batch_status[0]=(f"Dhan LTP partial: {received}/{total_symbols} • previous quotes retained • "
                                   +snapshot_age_label+"exchange timestamp unverified"
                                   if dhan_batch_issue[0] else
                                   f"Dhan LTP loaded: {received}/{total_symbols} valid prices • "+snapshot_age_label
                                   +f"polled {datetime.now().strftime('%H:%M:%S')} • exchange timestamp unverified")
            market_status=watch_batch_status[0]
            watch_batch_last_success[0]=time.monotonic()
        except Exception as exc:
            # Android may suspend a network request when the app loses focus.
            # Do not report that lifecycle interruption as a provider failure.
            if generation!=provider_generation[0] or prefs.get("source")!="Dhan":
                return
            # Interrupted and failed polls cannot certify that an old quote is live.
            # Retain valid same-provider prices, but downgrade their freshness.
            for ticker,old in list(quotes.items()):
                if (isinstance(old,dict) and old.get("source")=="Dhan"
                        and isinstance(old.get("price"),(int,float))
                        and not isinstance(old.get("price"),bool)
                        and math.isfinite(old["price"]) and old["price"]>0):
                    quotes[ticker]=dict(old,freshness="unverified",live_verified=False)
            if not app_active[0]:
                watch_batch_status[0]="Dhan quote refresh interrupted in background • retry on resume"
                return
            log_error("watchlist_dhan_batch",exc)
            with dhan_batch_lock:
                dhan_batch_cache.update(generation=None,updated=0.0,quotes={})
            # A failed poll must not blank the last valid displayed Dhan prices.
            dhan_batch_issue[0]=safe_error(exc)
            watch_batch_status[0]="Dhan batch failed: "+safe_error(exc)
            market_status=watch_batch_status[0]
        finally:
            watch_batch_busy[0]=False
            request_view_refresh(4)
    index_refresh_busy=[False]
    index_last_attempt=[0.0]
    index_refresh_generation=[None]
    async def refresh_dhan_index_quotes(force=False):
        """One serialized three-index cycle, independently throttled from equity snapshots."""
        if not app_active[0] or prefs.get("source")!="Dhan" or not dhan_feed.connected:
            return
        if index_refresh_busy[0]:
            return
        generation=provider_generation[0]
        now=time.monotonic()
        if (not force and index_refresh_generation[0]==generation
                and now-index_last_attempt[0]<60):
            return
        index_refresh_busy[0]=True
        index_last_attempt[0]=now
        index_refresh_generation[0]=generation
        try:
            snapshots=await asyncio.to_thread(dhan_feed.index_batch_quotes)
            if not app_active[0] or generation!=provider_generation[0] or prefs.get("source")!="Dhan":
                return
            for ticker in ("NIFTY", "BANKNIFTY", "SENSEX"):
                snapshot=snapshots.get(ticker)
                if snapshot is None:
                    # A successful batch can omit BSE_I quotes. Preserve the last
                    # known Dhan price, but explicitly mark provider unavailability.
                    old=quotes.get(ticker)
                    if isinstance(old,dict) and old.get("source")=="Dhan":
                        quotes[ticker]=dict(old,provider_status="provider_data_unavailable",
                            freshness="unverified",live_verified=False)
                    continue
                price=snapshot.get("price")
                if (snapshot.get("source")=="Dhan"
                        and isinstance(price,(int,float)) and not isinstance(price,bool)
                        and math.isfinite(price) and price>0):
                    old=quotes.get(ticker) or {}
                    quotes[ticker]=dict(snapshot,change=None,
                        bars=old.get("bars",[]) if old.get("source")=="Dhan" else [],
                        fetched_at=time.time(),live_verified=False)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log_error("dhan_index_ltp_batch",exc)
            for ticker in ("NIFTY", "BANKNIFTY", "SENSEX"):
                old=quotes.get(ticker)
                if isinstance(old,dict) and old.get("source")=="Dhan":
                    quotes[ticker]=dict(old,freshness="unverified",live_verified=False)
        finally:
            index_refresh_busy[0]=False
            if current[0] in (0,4,5):
                request_view_refresh(current[0])

    manual_quote_last_attempt=[0.0]
    async def refresh_all_dhan_quotes():
        if prefs.get("source")!="Dhan" or not dhan_feed.connected or watch_batch_busy[0] or index_refresh_busy[0]:
            return
        now=time.monotonic()
        remaining=max(0,30-(now-manual_quote_last_attempt[0]))
        if remaining>0:
            watch_batch_status[0]=f"Manual refresh available in {remaining:.0f}s • last valid prices retained"
            request_view_refresh(4)
            return
        cooldown=dhan_feed.cooldown_remaining("/v2/snapshot")
        if cooldown>0:
            watch_batch_status[0]=f"Dhan snapshot cooling down • retry in {cooldown:.0f}s • last valid prices retained"
            request_view_refresh(4)
            return
        manual_quote_last_attempt[0]=now
        await refresh_watch_batch()
        await refresh_dhan_index_quotes(force=True)

    quote_auto_last_attempt=[0.0]
    async def dhan_quote_poll():
        # BK-102: allow the app to settle before its first quote request.
        # Subsequent automatic polls remain on a 180-second cadence.
        await asyncio.sleep(10)
        while True:
            try:
                if (app_active[0] and prefs.get("source")=="Dhan" and dhan_feed.connected
                        and time.monotonic()-quote_auto_last_attempt[0]>=30
                        and not watch_batch_busy[0] and not index_refresh_busy[0]):
                    quote_auto_last_attempt[0]=time.monotonic()
                    remaining=dhan_feed.cooldown_remaining("/v2/snapshot")
                    if remaining==0:
                        await refresh_watch_batch()
                        if current[0]==0:
                            request_view_refresh(0)
                    elif not watch_batch_busy[0]:
                        watch_batch_status[0]=(
                            f"Dhan snapshot cooling down • retry in {remaining:.0f}s • "
                            "last valid prices retained; freshness unverified")
                        request_view_refresh(4)
                    await refresh_dhan_index_quotes()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log_error("dhan_quote_poll",exc)
            # Before Dhan connects, retry the first snapshot after 10s, not 3m.
            await asyncio.sleep(180 if quote_auto_last_attempt[0] else 10)

    async def watch_visible_tick():
        # Never rebuild the scrolling list every two seconds when quotes are unchanged.
        # The quote batch and scroll handler already request a view refresh.
        # Rebuilding all rows continuously resets Android scroll position.
        last_visible_signature=None
        while True:
            await asyncio.sleep(2)
            if current[0]!=4 or not app_active[0]:
                last_visible_signature=None
                continue
            try:
                visible=tuple(watch_groups[active_watch[0]])+("NIFTY","BANKNIFTY","SENSEX")
                signature=(active_watch[0],watch_batch_status[0],scan_progress.get("state"),tuple((sym,(quotes.get(sym) or {}).get("fetched_at"),
                            (quotes.get(sym) or {}).get("price"),
                            (watch_signal_cache.get(sym) or {}).get("timestamp")) for sym in visible))
                if signature!=last_visible_signature:
                    last_visible_signature=signature
                    fill_watch()
            except Exception as exc:log_error("watch_visible_tick",exc)

    def watchlist():
        fill_watch()
        index_symbols=("NIFTY", "BANKNIFTY", "SENSEX")
        index_cards=[]
        for index_name in index_symbols:
            index_quote=quotes.get(index_name) or {}
            valid=(prefs.get("source")=="Dhan" and index_quote.get("source")=="Dhan"
                   and isinstance(index_quote.get("price"),(int,float))
                   and not isinstance(index_quote.get("price"),bool)
                   and math.isfinite(index_quote["price"]) and index_quote["price"]>0)
            provider_missing=index_quote.get("provider_status")=="provider_data_unavailable"
            index_history=(chart_snapshots.get((index_name,"5m",provider_generation[0]))
                           or candles.get("scanner_chart_"+index_name) or {})
            index_signal_row=historical_vote_bar(historical_vote_agreement(index_history))
            index_cards.append(ft.Container(
                content=ft.Column([txt(index_name,11,WHITE,True),
                    txt(f'{index_quote["price"]:,.2f}' if valid else "—",14,MUTED if provider_missing else GOLD if valid else MUTED,True),
                    note(("Dhan unavailable • LAST KNOWN, not live" if valid else "Dhan index provider unavailable") if provider_missing else
                         ("Dhan LTP • cached/unverified" if time.time()-index_quote.get("fetched_at",0)>120 else "Dhan LTP • exchange time unverified") if valid else "Dhan LTP unavailable"),index_signal_row],
                    spacing=3),bgcolor=PANEL,border_radius=9,padding=8,expand=True,
                on_click=lambda e,v=index_name:open_stock(v)))
        return [heading("Watchlist • 5 Lists"),
            note("Market indexes (3) + equity universe ("+str(len(watch_symbols))+") = "+str(len(watch_symbols)+3)+" instruments • indexes excluded from equity scan"),
            ft.Column(index_cards,spacing=8),
            ft.Row([ft.Container(content=ft.TextButton("List "+str(i+1),on_click=lambda e,k=i:change_watch(k),style=ft.ButtonStyle(color=GOLD if active_watch[0]==i else MUTED,padding=2)),expand=True) for i in range(5)],spacing=0),
            note("List "+str(active_watch[0]+1)+" • "+str(len(watch_groups[active_watch[0]]))+" symbols • tap a row for details"),
            ft.Row([search,ft.IconButton(icon=ft.Icons.CLOSE,tooltip="Clear search",on_click=clear_watch_search)],spacing=2),note("Bullish/Bearish filters use fresh candle-filter votes, not daily price movement. Neutral includes unavailable signals."),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:set_filter(v),style=ft.ButtonStyle(color=GOLD if watch_filter[0]==n else MUTED)) for n in ["All","Bullish","Bearish","Neutral"]],scroll=ft.ScrollMode.AUTO),
            ft.Row([add_symbol,ft.ElevatedButton("Add",on_click=add_watch,bgcolor=GOLD,color=BG)]),feedback,
            note(("Dhan quote refresh • every 180 sec while foreground • "+watch_batch_status[0]) if prefs.get("source")=="Dhan" else market_status+" • Quotes may be delayed"),
            note("Candle scan • "+str(scan_progress.get("state","Not started"))+" • "+str(scan_progress.get("valid",0))+" valid / "+str(scan_progress.get("failed",0))+" failed • candle signals are independent of LTP refresh") if prefs.get("source")=="Dhan" else note(""),
            ft.Row([ft.ElevatedButton("Refresh Dhan LTP",on_click=lambda e:page.run_task(refresh_all_dhan_quotes),
                disabled=watch_batch_busy[0] or prefs.get("source")!="Dhan"),
                note(watch_batch_status[0] if prefs.get("source")=="Dhan" else "Select Dhan for batch quotes")],
                wrap=True),note("Quote refresh is independent of historical analysis • latest batch status above"),watch_list]
    symbol=ft.Dropdown(label="Symbol",value=prefs.get("chart_symbol","NIFTY"),options=[ft.dropdown.Option(x) for x in selection_symbols()],expand=True)
    timeframe=ft.Dropdown(label="Timeframe",value=prefs.get("chart_timeframe","5m") if prefs.get("chart_timeframe","5m") in ("1m","5m","15m","1h") else "5m",options=[ft.dropdown.Option(x) for x in ["1m","5m","15m","1h"]],width=120)
    ema=ft.Switch(label="EMA 20 / 50",value=bool(prefs.get("chart_ema",True)),active_color=GREEN)
    vwap=ft.Switch(label="VWAP",value=bool(prefs.get("chart_vwap",True)),active_color=GREEN)
    rsi=ft.Switch(label="RSI",value=bool(prefs.get("chart_rsi",False)),active_color=GREEN)
    chart_tab=["Chart"]
    drawing_mode=["None"]
    compare_choices=(["NIFTY","RELIANCE","HDFCBANK","ICICIBANK"] if prefs.get("source","Dhan")=="Dhan" else ["NIFTY","BANKNIFTY","SENSEX","RELIANCE","HDFCBANK"])
    compare_symbol=ft.Dropdown(label="Compare",value="RELIANCE" if prefs.get("source","Dhan")=="Dhan" else "BANKNIFTY",options=[ft.dropdown.Option(x) for x in compare_choices])
    macd=ft.Switch(label="MACD (12,26,9)",value=bool(prefs.get("chart_macd",False)),active_color=GREEN)
    volume=ft.Switch(label="Volume",value=bool(prefs.get("chart_volume",True)),active_color=GREEN)
    ema200=ft.Switch(label="EMA 200",value=bool(prefs.get("chart_ema200",False)),active_color=GREEN)
    sma50=ft.Switch(label="SMA 50",value=bool(prefs.get("chart_sma50",False)),active_color=GREEN)
    bollinger=ft.Switch(label="Bollinger Bands",value=bool(prefs.get("chart_bollinger",False)),active_color=GREEN)
    atr=ft.Switch(label="ATR 14",value=bool(prefs.get("chart_atr",False)),active_color=GREEN)
    supertrend=ft.Switch(label="Supertrend",value=bool(prefs.get("chart_supertrend",False)),active_color=GREEN)
    def persist_chart_settings(e=None):
        prefs.update({"chart_ema":ema.value,"chart_vwap":vwap.value,"chart_rsi":rsi.value,"chart_macd":macd.value,"chart_volume":volume.value,"chart_ema200":ema200.value,"chart_sma50":sma50.value,"chart_bollinger":bollinger.value,"chart_atr":atr.value,"chart_supertrend":supertrend.value})
        prefs.update(chart_symbol=symbol.value,chart_timeframe=timeframe.value,chart_type=prefs.get("chart_type","Candlestick"))
        saved=save()
        if e is not None:
            chart_message.value="Chart preferences saved." if saved else "Could not save chart preferences."
            page.update()
    for control in [ema,vwap,rsi,macd,volume,ema200,sma50,bollinger,atr,supertrend]:
        control.on_change=persist_chart_settings
    chart_message=txt("",12,MUTED)
    def choose_chart_tab(v):
        chart_tab[0]=v
        select(5)
    chart_style=[prefs.get("chart_type","Candlestick")]
    chart_style_picker=ft.Dropdown(label="Chart type",value=prefs.get("chart_type","Candlestick"),options=[ft.dropdown.Option(x) for x in ["Candlestick","Line"]])
    def chart_selection_changed(e):
        persist_chart_settings(e)
        if current[0]==5:
            chart_message.value="Loading selected chart candles..."
            page.run_task(load_chart)
    symbol.on_change=chart_selection_changed
    timeframe.on_change=chart_selection_changed
    def chart_style_apply(e):
        chart_style[0]=chart_style_picker.value
        prefs["chart_type"]=chart_style_picker.value
        persist_chart_settings()
        select(5)
    chart_snapshots={}
    def chart_snapshot(sym):
        return chart_snapshots.get((sym,timeframe.value,provider_generation[0])) or {}
    def chart_candles():
        q=chart_snapshot(symbol.value)
        bars=q.get("bars") or []
        if len(bars)<2:
            return ft.Container(content=ft.Column([ft.Icon(ft.Icons.CANDLESTICK_CHART,size=48,color=GOLD),txt("Candles loading / unavailable"),note("Selected provider candles unavailable • check source and refresh status")],horizontal_alignment=ft.CrossAxisAlignment.CENTER),height=210,alignment=ft.alignment.center)
        bars=bars[-36:]
        if chart_style[0]=="Line":
            return ft.Container(content=tiny_chart(symbol.value,chart_snapshot(symbol.value)),height=230)
        low=min(b[3] for b in bars);high=max(b[2] for b in bars)
        spread=max(high-low,.001)
        width=324; height=230
        controls=[]
        for i,(_,o,h,l,c,v) in enumerate(bars):
            x=i*width/len(bars)+2
            yhigh=10+(high-h)/spread*195
            ylow=10+(high-l)/spread*195
            yo=10+(high-o)/spread*195
            yc=10+(high-c)/spread*195
            color=GREEN if c>=o else RED
            controls.append(ft.Container(left=x+2,top=yhigh,width=2,height=max(1,ylow-yhigh),bgcolor=color))
            controls.append(ft.Container(left=x,top=min(yo,yc),width=max(3,width/len(bars)-2),height=max(2,abs(yc-yo)),bgcolor=color))
        # Fixed candle-derived reference guides, not interactive touch drawings.
        mode=drawing_mode[0]
        if mode=="Horizontal":
            y=10+(high-bars[-1][4])/spread*195
            controls.append(ft.Container(left=0,top=y,width=width,height=1,bgcolor=GOLD))
        elif mode=="Vertical":
            x=(len(bars)-1)*width/len(bars)+2
            controls.append(ft.Container(left=x,top=0,width=1,height=height,bgcolor=GOLD))
        elif mode=="Fibonacci":
            for ratio in (0.236,0.382,0.5,0.618,0.786):
                y=10+ratio*195
                controls.append(ft.Container(left=0,top=y,width=width,height=1,bgcolor=GOLD))
        guide=note("Guide: "+mode+" • candle-derived reference, not draggable") if mode in ("Horizontal","Vertical","Fibonacci") else note("Drawing overlays: none • touch drawing not implemented")
        return ft.Column([ft.Row([note(f"High {high:,.2f}"),note(f"Low {low:,.2f}")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Container(content=ft.Stack(controls,width=width,height=height),height=height),note(f"{q.get('source','Market')} OHLC • {timeframe.value} • verify feed freshness"),guide],spacing=3)
    def drawing_action(v):
        drawing_mode[0]="None" if v=="Clear" else v
        if v=="Trendline":
            chart_message.value="Trendline touch drawing is not implemented • no line added"
        elif v=="Clear":
            chart_message.value="Candle reference guides cleared"
        else:
            chart_message.value="Selected "+v+" • reference guide uses loaded candles; not draggable"
        select(5)
    chart_quantity=ft.TextField(label="Paper quantity",value="1",width=140,keyboard_type=ft.KeyboardType.NUMBER)
    chart_sl=ft.TextField(label="Stop loss % (paper)",value="2",width=150,keyboard_type=ft.KeyboardType.NUMBER)
    chart_target=ft.TextField(label="Target % (paper)",value="4",width=150,keyboard_type=ft.KeyboardType.NUMBER)
    chart_paper_status=txt("Paper trading • no real orders",12,MUTED)
    def open_positions():
        return prefs.setdefault("paper_positions",{})
    def trade_history():
        return prefs.setdefault("paper_history",[])
    def position_pnl(p):
        quote=quotes.get(p["symbol"]) or {}
        expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
        try:
            age=time.time()-float(quote.get("quote_timestamp"))
            price=finite(quote.get("price"),"Paper mark",.000001)
            if quote.get("source")!=expected or quote.get("cached") or not 0<=age<=90:
                return None
            return (price-float(p["entry"]))*int(p["qty"])*(1 if p["side"]=="BUY" else -1)
        except (ValueError,TypeError,OverflowError,KeyError):
            return None
    def exit_paper(sym):
        p=open_positions().pop(sym,None)
        if p:
            # Only record an exit P&L when the mark is positive, recent and from the active provider.
            quote=quotes.get(sym) or {}
            expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            try:
                age=time.time()-float(quote.get("quote_timestamp"))
                mark=finite(quote.get("price"),"Exit mark",.000001)
                valid=quote.get("source")==expected and not quote.get("cached") and 0<=age<=90
            except (ValueError,TypeError,OverflowError):
                valid=False;mark=None
            pnl=(mark-float(p["entry"]))*int(p["qty"])*(1 if p["side"]=="BUY" else -1) if valid else None
            trade_history().append({"event":"EXIT","symbol":sym,"side":p["side"],"qty":p["qty"],"price":mark if valid else None,"pnl":pnl,"time":datetime.now().isoformat(timespec="seconds"),"mark_status":"recent_provider_quote" if valid else "unknown"})
            ledger=paper_risk_ledger()
            if pnl is None:
                ledger["unknown_exits"]=int(ledger.get("unknown_exits",0))+1
            else:
                ledger["realized_loss"]=float(ledger.get("realized_loss",0))+max(0,-pnl)
            save()
        select(current[0])
    def chart_paper_trade(side):
        sym=symbol.value
        if side=="EXIT":
            if sym in open_positions():
                exit_paper(sym)
                chart_paper_status.value="Paper position closed."
            else:chart_paper_status.value="No open position for "+sym
        else:
            try:
                if mode.value!="Paper" or emergency_stop.value:
                    raise ValueError("Paper mode required and emergency stop must be off")
                quote=quotes.get(sym) or {}
                expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
                stamp=quote.get("quote_timestamp")
                age=time.time()-float(stamp) if stamp is not None else float("inf")
                if (quote.get("source")!=expected or quote.get("cached")
                        or not 0<=age<=90):
                    raise ValueError("Recent current-provider quote unavailable")
                qty=int(chart_quantity.value)
                price=finite(quote.get("price"),"Paper quote",.000001)
                sl_pct=float(chart_sl.value);target_pct=float(chart_target.value)
                if qty<1 or qty>100000 or price is None or not (0<sl_pct<=100 and 0<target_pct<=100):raise ValueError()
                if sym in open_positions():
                    chart_paper_status.value="Position already open for "+sym+". Exit first."
                    select(2)
                    return
                price=float(price)
                sl_price=price*(1-sl_pct/100 if side=="BUY" else 1+sl_pct/100)
                target_price=price*(1+target_pct/100 if side=="BUY" else 1-target_pct/100)
                validate_field(limit,"max_trades",limit.value)
                validate_field(max_daily_loss,"max_daily_loss",max_daily_loss.value)
                ledger=paper_risk_ledger()
                if int(ledger.get("unknown_exits",0))>0:
                    raise ValueError("Unknown paper exit P&L: reconcile daily risk before another entry")
                if int(ledger["entries"])>=int(limit.value):
                    raise ValueError("Daily paper entry limit reached")
                planned_risk=check_trade_risk(price,qty,sl_price)
                if float(ledger.get("realized_loss",0))>=float(max_daily_loss.value):
                    raise ValueError("Daily realized paper loss limit reached")
                if planned_risk>float(max_daily_loss.value)-float(ledger["planned_risk_used"])+1e-9:
                    raise ValueError("Daily paper planned-risk budget exceeded")
                ledger["entries"]+=1
                ledger["planned_risk_used"]+=planned_risk
                open_positions()[sym]={"symbol":sym,"side":side,"entry":price,"qty":qty,"sl":sl_price,"target":target_price,"time":datetime.now().isoformat(timespec="seconds")}
                trade_history().append({"event":side,"symbol":sym,"side":side,"qty":qty,"price":price,"time":datetime.now().isoformat(timespec="seconds")})
                saved=save()
                chart_paper_status.value="Paper "+side+" recorded"+(" and saved." if saved else " (storage unavailable).")
            except (ValueError,TypeError):
                chart_paper_status.value="Valid quantity, SL, target and available quote required."
        select(2)
    def chart_position_text():
        p=open_positions().get(symbol.value)
        if not p:return "Paper position: FLAT"
        pnl=position_pnl(p)
        return "Paper "+p["side"]+" "+p["symbol"]+" ×"+str(p["qty"])+" @ ₹"+format(p["entry"],",.2f")+" • "+("P&L unavailable" if pnl is None else "Unrealized P&L ₹"+format(pnl,",.2f"))
    def dashboard_positions():
        controls=[]
        total=0.0;missing=False
        for sym,p in open_positions().items():
            pnl=position_pnl(p)
            if pnl is None:missing=True
            else:total+=pnl
            controls.append(ft.Column([txt(sym+" • "+p["side"]+" ×"+str(p["qty"]),14,GOLD,True),note("Entry ₹"+format(p["entry"],",.2f")+" • SL ₹"+format(p["sl"],",.2f")+" • Target ₹"+format(p["target"],",.2f")),note("P&L unavailable" if pnl is None else "Unrealized P&L ₹"+format(pnl,",.2f")),ft.OutlinedButton("Exit "+sym,on_click=lambda e,v=sym:exit_paper(v))]))
        if not controls:controls.append(note("No open paper positions"))
        controls.append(txt("Total unrealized P&L "+("partially unavailable • " if missing else "")+"₹"+format(total,",.2f"),14,GOLD,True))
        history=trade_history()[-10:]
        controls.append(txt("Recent paper orders",15,GOLD,True))
        for h in reversed(history):
            controls.append(note(h.get("time","")+" • "+h.get("event","")+" "+h.get("symbol","")+" ×"+str(h.get("qty",""))))
        return section("My Positions • Paper Only",ft.Column(controls,spacing=9))
    def chart_analysis_panel(kind):
        quote=chart_snapshot(symbol.value)
        result=chart_indicators(quote.get("bars") or [])
        if result["status"]!="AVAILABLE":
            return section(kind,note("Analysis unavailable: "+result["reason"]))
        def fmt(key):return format(result[key],",.2f")
        stamp=datetime.fromtimestamp(result["timestamp"],timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M IST")
        provenance=note(str(quote.get("source","Unknown"))+" • "+stamp+" • "+str(result["count"])+" candles • check data freshness before trading")
        if kind=="Market Levels":
            return section(kind,ft.Column([txt("20-candle rolling support ₹"+fmt("support"),14,GREEN),txt("20-candle rolling resistance ₹"+fmt("resistance"),14,RED),note("ATR14 ₹"+fmt("atr14")+" • calculated zones, not verified exchange levels"),provenance],spacing=5))
        return section(kind,ft.Column([txt("Candle analysis: "+result["bias"],16,GOLD,True),note("EMA20 ₹"+fmt("ema20")+" • EMA50 ₹"+fmt("ema50")+" • RSI14 "+fmt("rsi14")),note(result["reason"]+" • not an order recommendation"),provenance],spacing=5))
    def charts():
        content=[heading("Charts • Technical Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_chart_tab(v),style=ft.ButtonStyle(color=GOLD if chart_tab[0]==n else MUTED)) for n in ["Chart","Indicators","Drawing","Compare","Levels","Signals"]],scroll=ft.ScrollMode.AUTO),ft.Row([symbol,timeframe]),ft.ElevatedButton("Apply / Refresh",on_click=lambda e:page.run_task(load_chart),bgcolor=GOLD,color=BG)]
        if chart_tab[0]=="Chart":
            content.append(section("Stock Details • "+symbol.value,ft.Column([
                txt("₹ "+quote_price(symbol.value),26,GOLD,True),
                txt("Change "+quote_change(symbol.value),14,price_color(symbol.value),True),
                note(quote_caption(symbol.value)),chart_message,
                ft.Row([chart_quantity,chart_sl,chart_target],wrap=True),
                ft.Row([ft.ElevatedButton("BUY • Paper",on_click=lambda e:chart_paper_trade("BUY"),bgcolor=GREEN,color=BG),ft.ElevatedButton("SELL • Paper",on_click=lambda e:chart_paper_trade("SELL"),bgcolor=RED,color=BG),ft.OutlinedButton("Exit",on_click=lambda e:chart_paper_trade("EXIT"))],wrap=True),
                txt(chart_position_text(),12,GOLD),chart_paper_status,
                note("Simulation only • no real orders")
            ])))
            content.extend([ft.Row([chart_style_picker,ft.ElevatedButton("Set chart type",on_click=chart_style_apply)]),section("Candlestick Chart",chart_candles()),section("Price Trend",ft.Container(content=tiny_chart(symbol.value,chart_snapshot(symbol.value)),height=120)),ft.Row([ft.TextButton("Indicators",on_click=lambda e:choose_chart_tab("Indicators")),ft.TextButton("Drawing",on_click=lambda e:choose_chart_tab("Drawing"))])])
        elif chart_tab[0]=="Indicators":
            selected=[n for n,c in [("EMA20/50",ema),("EMA200",ema200),("VWAP",vwap),("RSI",rsi),("MACD",macd),("Volume",volume),("SMA50",sma50),("Bollinger",bollinger),("ATR14",atr),("Supertrend",supertrend)] if c.value]
            indicator_rows=[ema,ema200,sma50,bollinger,vwap,rsi,macd,volume,atr,supertrend,
                            ft.ElevatedButton("Save indicators",on_click=lambda e:persist_chart_settings(e)),
                            note("Selected: "+(", ".join(selected) if selected else "None"))]
            snapshot=chart_snapshot(symbol.value)
            expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            if snapshot.get("source")!=expected:
                indicator_rows.append(note("Indicator values unavailable • selected provider data not loaded"))
            else:
                result=chart_indicators(snapshot.get("bars") or [])
                if result.get("status")!="AVAILABLE":
                    indicator_rows.append(note("Indicator values unavailable • "+str(result.get("reason","insufficient candles"))))
                else:
                    indicator_rows.append(note("Computed from "+str(result["count"])+" validated candles • "+
                                               str(snapshot.get("freshness","unverified"))+" • not verified live"))
                    if ema.value:
                        indicator_rows.append(note("EMA20: "+format(result["ema20"],",.2f")+" • EMA50: "+format(result["ema50"],",.2f")))
                    if rsi.value:
                        indicator_rows.append(note("RSI14: "+format(result["rsi14"],".2f")))
                    if atr.value:
                        indicator_rows.append(note("ATR14: "+format(result["atr14"],",.2f")))
            unsupported=[n for n,c in [("EMA200",ema200),("SMA50",sma50),("Bollinger",bollinger),
                                         ("VWAP",vwap),("MACD",macd),("Volume overlay",volume),
                                         ("Supertrend",supertrend)] if c.value]
            if unsupported:
                indicator_rows.append(note("Not calculated/displayed on this chart: "+", ".join(unsupported)))
            indicator_rows.append(note("Indicator overlays are not drawn on the candlestick chart yet."))
            content.append(section("Indicators • Toggle On / Off",ft.Column(indicator_rows,spacing=5)))
        elif chart_tab[0]=="Drawing":
            content.append(section("Drawing Tools",ft.Column([ft.Row([ft.ElevatedButton(x,on_click=lambda e,v=x:drawing_action(v)) for x in ["Trendline","Horizontal","Vertical"]],wrap=True),ft.Row([ft.ElevatedButton(x,on_click=lambda e,v=x:drawing_action(v)) for x in ["Fibonacci","Clear"]],wrap=True),note("Horizontal: latest candle close • Vertical: latest candle • Fibonacci: visible high/low range • Trendline touch drawing unavailable"),note("Switch to Chart tab to see candle reference guides; not draggable."),chart_message])))
        elif chart_tab[0]=="Compare":
            peer=compare_symbol.value
            peer_quote=chart_snapshot(peer)
            current_quote=chart_snapshot(symbol.value)
            peer_bars=peer_quote.get("bars") or []
            base_bars=current_quote.get("bars") or []
            peer_source=peer_quote.get("source")
            expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            comparison=[compare_symbol,ft.ElevatedButton("Compare / Refresh",on_click=lambda e:page.run_task(load_comparison))]
            if peer==symbol.value:
                comparison.append(note("Choose a different symbol to compare."))
            elif peer_source!=expected or len(peer_bars)<2 or current_quote.get("source")!=expected or len(base_bars)<2:
                comparison.append(note("Comparison unavailable • both symbols require verified provider candle history"))
            else:
                comparison.extend([note(symbol.value+" • "+str(len(base_bars))+" candles • "+str(current_quote.get("freshness","unverified"))),
                                   ft.Container(content=tiny_chart(symbol.value),height=120),
                                   note(peer+" • "+str(len(peer_bars))+" candles • "+str(peer_quote.get("freshness","unverified"))),
                                   ft.Container(content=tiny_chart(peer,peer_quote),height=120),
                                   note("Separate price trends • not normalized returns or a live signal")])
            comparison.append(chart_message)
            content.append(section("Compare Symbols",ft.Column(comparison,spacing=5)))
        elif chart_tab[0]=="Levels":
            content.append(chart_analysis_panel("Market Levels"))
        else:
            content.append(chart_analysis_panel("Signals"))
        return content
    chart_load_busy=[False]
    chart_load_pending=[False]
    async def load_chart():
        if chart_load_busy[0]:
            # Queue the latest selection instead of silently dropping it.
            chart_load_pending[0]=True
            chart_message.value="Chart request queued for latest selection..."
            page.update()
            return
        chart_load_busy[0]=True
        sym=symbol.value;tf=timeframe.value;generation=provider_generation[0]
        try:
            chart_message.value="Loading "+str(sym)+" "+str(tf)+" candles..."
            if current[0]==5:page.update()
            data=await asyncio.to_thread(get_market_data,sym,tf,"5d" if tf in ["1m","5m","15m"] else "1mo")
            if generation!=provider_generation[0] or sym!=symbol.value or tf!=timeframe.value:
                return
            chart_snapshots[(sym,tf,generation)]=data
            bars=data.get("bars") or []
            chart_message.value=("Chart updated • "+str(data.get("source","unknown"))+
                                 " • "+str(len(bars))+" candles • "+str(data.get("freshness","unverified"))+
                                 " • verify timestamp before trading")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log_error("load_chart",exc)
            chart_message.value=prefs.get("source","Market")+" candles unavailable: "+safe_error(exc)+" • last available chart retained if cached"
        finally:
            chart_load_busy[0]=False
            if current[0]==5:request_view_refresh(5)
            if chart_load_pending[0]:
                chart_load_pending[0]=False
                if current[0]==5 and (sym!=symbol.value or tf!=timeframe.value or generation!=provider_generation[0]):
                    page.run_task(load_chart)
    async def load_comparison():
        peer=compare_symbol.value
        tf=timeframe.value
        generation=provider_generation[0]
        if peer==symbol.value:
            chart_message.value="Choose a different symbol to compare."
            select(5)
            return
        if prefs.get("source","Dhan")=="Dhan" and peer not in DHAN_VERIFIED_SYMBOLS:
            chart_message.value="Dhan comparison mapping not verified for "+str(peer)[:32]
            select(5)
            return
        try:
            data=await asyncio.to_thread(get_market_data,peer,tf,"5d" if tf in ("1m","5m","15m") else "1mo")
            if generation!=provider_generation[0] or peer!=compare_symbol.value or tf!=timeframe.value:
                return
            chart_snapshots[(peer,tf,generation)]=data
            chart_message.value=peer+" comparison loaded • "+str(len(data.get("bars") or []))+" candles • "+str(data.get("freshness","unverified"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log_error("chart_comparison",exc)
            chart_message.value="Comparison data unavailable: "+safe_error(exc)
        finally:
            if current[0]==5:request_view_refresh(5)
    chain_symbol=ft.Dropdown(label="Index / Stock",value=prefs.get("option_symbol","NIFTY"),options=[ft.dropdown.Option(x) for x in selection_symbols()])
    option_add_symbol=ft.TextField(label="Add symbol",hint_text="e.g. HDFCBANK")
    option_expiry_choice=ft.Dropdown(label="Expiry",value=prefs.get("option_expiry_choice","Nearest"),options=[ft.dropdown.Option(x) for x in ["Nearest","Next","Manual"]])
    expiry=ft.TextField(label="Expiry date (calendar preview)",value=prefs.get("option_expiry",""),read_only=True)
    option_expiry_note=txt("Calendar estimate only; holidays and listed contracts need broker/exchange verification.",11,GOLD)
    def monthly_expiry(year,month,weekday):
        import calendar
        last=calendar.monthrange(year,month)[1]
        d=date(year,month,last)
        return d-timedelta(days=(d.weekday()-weekday)%7)
    def option_dates(sym,now=None):
        now=now or datetime.now(timezone(timedelta(hours=5,minutes=30)))
        today=now.date()
        def eligible(d):
            return d>today or (d==today and (now.hour,now.minute)<(15,30))
        weekly=sym in ("NIFTY","SENSEX")
        day=3 if sym=="SENSEX" else 1
        result=[]
        if weekly:
            for i in range(0,40):
                d=today+timedelta(days=i)
                if d.weekday()==day and eligible(d):result.append(d)
                if len(result)>=2:break
        else:
            for i in range(0,6):
                y=today.year+(today.month-1+i)//12
                m=(today.month-1+i)%12+1
                d=monthly_expiry(y,m,day)
                if eligible(d):result.append(d)
                if len(result)>=2:break
        return result
    def refresh_option_expiry(e=None):
        if option_expiry_choice.value=="Manual":
            expiry.read_only=False
        else:
            expiry.read_only=True
            dates=option_dates(chain_symbol.value)
            idx=1 if option_expiry_choice.value=="Next" else 0
            expiry.value=dates[idx].isoformat() if len(dates)>idx else ""
        prefs.update(option_symbol=chain_symbol.value,option_expiry_choice=option_expiry_choice.value,option_expiry=expiry.value or "")
        save()
        if e is not None:select(1)
    def add_option_symbol(e):
        sym=(option_add_symbol.value or "").strip().upper().replace(".NS","")
        if sym and sym.replace("-","").replace("&","").isalnum() and sym not in [o.key for o in chain_symbol.options]:
            chain_symbol.options.append(ft.dropdown.Option(sym))
            prefs["custom_symbols"]=list(dict.fromkeys(prefs.get("custom_symbols",[])+[sym]))
            sync_symbol_choices()
        if sym and sym in [o.key for o in chain_symbol.options]:
            chain_symbol.value=sym
            option_add_symbol.value=""
            refresh_option_expiry()
        select(1)
    chain_symbol.on_change=refresh_option_expiry
    option_expiry_choice.on_change=refresh_option_expiry
    if chain_symbol.value not in [o.key for o in chain_symbol.options]:chain_symbol.options.append(ft.dropdown.Option(chain_symbol.value))
    refresh_option_expiry()
    option_tab=[prefs.get("option_tab","Option Chain")]
    if option_tab[0] not in ("Option Chain","OI Analysis","PCR","Premium Flow","Strategy"):option_tab[0]="Option Chain"
    strategy_choice=[prefs.get("option_strategy","")]
    option_notice=txt("",12,MUTED)
    def choose_option_tab(v):
        option_tab[0]=v
        prefs["option_tab"]=v;save()
        select(1)
    def choose_strategy(v):
        strategy_choice[0]=v
        prefs["option_strategy"]=v;save()
        select(1)
    option_strike=ft.TextField(label="Strike price",value=prefs.get("option_strike",""),hint_text="e.g. 25000",keyboard_type=ft.KeyboardType.NUMBER)
    option_side=ft.Dropdown(label="Contract",value=prefs.get("option_side","CE"),options=[ft.dropdown.Option("CE"),ft.dropdown.Option("PE")])
    option_qty=ft.TextField(label="Lots (paper)",value=str(prefs.get("option_qty","1")),keyboard_type=ft.KeyboardType.NUMBER)
    option_paper_note=txt("Option paper entry requires verified premium and lot size.",12,MUTED)
    def option_paper_action(side):
        option_paper_note.value="Cannot "+side+": verified CE/PE premium, listed strike and lot size unavailable. No order placed."
        page.update()
    option_chart_cache={}
    option_chart_busy=[False]
    option_chart_feedback={}
    def option_chart_context():
        return (chain_symbol.value,expiry.value,option_strike.value,option_side.value)
    async def load_option_history():
        if option_chart_busy[0]:return
        context=option_chart_context();generation=provider_generation[0]
        key=(generation,context)
        message=""
        if prefs.get("source")!="Broker API" or not angel_feed.connected:
            message="Select Broker API and connect Angel One in Settings to load verified option premium history."
        else:
            try:
                if finite(context[2])<=0:raise ValueError("strike")
                date.fromisoformat(context[1])
            except (ValueError,TypeError):
                message="Enter a positive listed strike and select a broker-listed expiry, then load the chart."
        if message:
            option_chart_feedback.update(key=key,state="UNAVAILABLE",message=message)
            if current[0]==1:select(1)
            return
        option_chart_busy[0]=True
        option_chart_feedback.update(key=key,state="LOADING",message="Loading selected option history from Angel One...")
        health_key="option_chart:"+":".join(str(x) for x in context);request_id=health.begin(health_key)
        if current[0]==1:select(1)
        try:
            raw_bars=await asyncio.to_thread(angel_feed.option_history,*context)
            if generation!=provider_generation[0] or context!=option_chart_context():return
            bars=clean_bars(raw_bars)
            if len(bars)<2:raise FeedError("Not enough valid option candles")
            option_chart_cache.clear();option_chart_cache.update(context=context,bars=bars)
            market_store.put("option_chart",context,{"bars":bars,"source":"Angel One"})
            state="AVAILABLE" if 0<=datetime.now(timezone.utc).timestamp()-bars[-1][0]<=630 else "STALE"
            health.finish(health_key,request_id,state,source="Angel One",data_time=bars[-1][0])
            option_chart_feedback.update(key=key,state=state,message="Selected option premium history loaded from Angel One.")
        except Exception as exc:
            log_error("option_chart",exc)
            if generation==provider_generation[0] and context==option_chart_context():
                health.finish(health_key,request_id,"UNAVAILABLE",error=safe_error(exc))
                option_chart_feedback.update(key=key,state="UNAVAILABLE",message="Angel One option history request failed: "+safe_error(exc)+". Verify the selected listed contract and server session, then retry.")
        finally:
            option_chart_busy[0]=False
            if current[0]==1:select(1)
    def option_chart_panel():
        context=option_chart_context()
        feedback=option_chart_feedback if option_chart_feedback.get("key")== (provider_generation[0],context) else {}
        controls=[note("Option premium history • selected manual strike / CE or PE • 5m"),ft.ElevatedButton("Load option premium chart",disabled=option_chart_busy[0],on_click=lambda e:page.run_task(load_option_history))]
        bars=option_chart_cache.get("bars",[]) if option_chart_cache.get("context")==context else (market_store.get("option_chart",*context) or {}).get("bars",[])
        bars=clean_bars(bars)
        if bars:
            series=ft.LineChartData(data_points=[ft.LineChartDataPoint(i,b[4]) for i,b in enumerate(bars[-70:])],color=GOLD,stroke_width=2)
            controls.append(ft.Container(content=ft.LineChart(data_series=[series],expand=True),height=200))
            controls.append(note("Angel One • last available history • "+age_label(bars[-1][0])+" • last candle: "+datetime.fromtimestamp(bars[-1][0],timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M IST")))
        if feedback:
            controls.append(unavailable(feedback["message"]) if feedback["state"]=="UNAVAILABLE" else note(feedback["message"]))
        elif not bars:
            if not angel_feed.connected:message="Connect Angel One in Settings to load option premium history."
            else:message="Enter a listed strike, choose CE or PE, then press Load option premium chart."
            controls.append(note(message))
        return section("Option Chart",ft.Column(controls,horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    def quote_caption(sym):
        if dhan_offline():return "Dhan disconnected • saved prices hidden • connect to verify"
        q=quotes.get(sym) or {}
        stamp=q.get("quote_timestamp");source_name=q.get("source","No data")
        # A recent timestamp alone does not prove exchange-verified live data.
        if source_name=="Dhan" and q.get("freshness")!="exchange_verified":
            return "Dhan • "+("quote timestamp unavailable" if not stamp else "quote timestamp unverified")+" • NOT VERIFIED LIVE"
        if not stamp:return source_name+" • quote timestamp unavailable • NOT VERIFIED LIVE"
        try:
            age=datetime.now(timezone.utc).timestamp()-float(stamp)
            when=datetime.fromtimestamp(float(stamp),timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M:%S IST")
            return source_name+" • "+("Last saved quote" if q.get("cached") else "Recent quote" if 0<=age<=90 else "Old / delayed quote")+" • "+when+" • "+age_label(float(stamp))
        except (ValueError,TypeError,OverflowError):return source_name+" • invalid timestamp"
    def data_source_panel(page_id=None):
        chooser=ft.Dropdown(label="Market data mode",value="Dhan",
            options=[ft.dropdown.Option("Dhan")])
        def changed(e):
            # Ignore any stale/non-Dhan control event from an older saved UI.
            if e.control.value!="Dhan":return
            source.value="Dhan"
            source.on_change(type("SourceChange",(),{"control":source})())
            page.run_task(refresh_selected_options)
        chooser.on_change=changed
        sym=chain_symbol.value if (current[0] if page_id is None else page_id)==1 else (scan_symbol.value or "NIFTY")
        return section("DATA SOURCE",ft.Column([chooser,note(quote_caption(sym)),
            note("Dhan read-only quotes, candles and NIFTY option metrics. Option freshness unverified; signals and live orders OFF.")],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    async def refresh_selected_options():
        # Dhan-only read-only option metrics. No Angel One fallback.
        if option_feed_busy[0] or not dhan_feed.connected:
            option_feed_status[0]="Connect Dhan in Settings to load listed option expiries."
            return
        option_feed_busy[0]=True
        dhan_option_last_attempt[0]=time.monotonic()
        generation=provider_generation[0]
        sym=chain_symbol.value
        choice=option_expiry_choice.value
        health_key="options:"+sym
        request_id=health.begin(health_key)
        option_feed_status[0]="Loading broker-listed Dhan expiries..."
        try:
            if sym!="NIFTY":
                raise FeedError("Dhan option-chain mapping is currently verified only for NIFTY")
            dates=await asyncio.to_thread(dhan_feed.option_expiries,sym)
            if generation!=provider_generation[0] or sym!=chain_symbol.value or choice!=option_expiry_choice.value:return
            if choice=="Manual":
                chosen=expiry.value
                if chosen not in dates:
                    raise FeedError("Selected expiry is not broker-listed; choose Nearest or Next")
            else:
                index=1 if choice=="Next" else 0
                if index>=len(dates):raise FeedError("Next broker-listed expiry unavailable")
                chosen=dates[index]
            expiry.value=chosen
            expiry.read_only=choice!="Manual"
            prefs["option_expiry"]=chosen
            save()
            option_expiry_note.value="Dhan broker-listed expiry • "+chosen+" • no calendar estimate"
            # Preserve the latest verified underlying LTP: historical candles must
            # never overwrite a newer quote snapshot.
            previous=quotes.get(sym) or {}
            # No history request is needed for option metrics.
            option_feed_status[0]="Loading Dhan read-only PCR and Max Pain..."
            data=await asyncio.to_thread(dhan_feed.option_chain_metrics,sym,chosen)
            if generation!=provider_generation[0] or sym!=chain_symbol.value or choice!=option_expiry_choice.value or expiry.value!=chosen:return
            dhan_option_metrics.clear()
            dhan_option_metrics.update(data)
            option_feed.clear()  # Do not show legacy Angel One contract rows.
            option_snapshots.pop(sym,None)  # Unverified metrics must not drive signals.
            option_feed_status[0]="Dhan • expiry "+chosen+" • freshness unverified • signals and live orders OFF"
            health.finish(health_key,request_id,"PARTIAL",source="Dhan",error="Option metrics unverified; signals disabled")
        except Exception as exc:
            log_error("dhan_options",exc)
            health.finish(health_key,request_id,"UNAVAILABLE",error=safe_error(exc))
            option_feed_status[0]="Dhan options unavailable: "+safe_error(exc)
            # Keep last valid metrics for historical display, never for signals.
        finally:
            option_feed_busy[0]=False
            if current[0]==1:select(1)
    async def option_poll():
        while True:
            if not app_active[0]:
                await asyncio.sleep(5);continue
            if current[0]==1 and regular_hours() and time.monotonic()-dhan_option_last_attempt[0]>=60:await refresh_selected_options()
            elif current[0] in (0,3) and regular_hours():
                sym=scan_symbol.value or "NIFTY";generation=provider_generation[0]
                try:
                    hist=await asyncio.to_thread(get_market_data,sym,scan_tf.value or "5m",scan_period.value or "7d")
                    if generation==provider_generation[0] and sym==scan_symbol.value:
                        quotes[sym]=hist
                        if current[0]==0:request_view_refresh(0)
                except Exception as exc:log_error("selected_quote",exc)
            await asyncio.sleep(15)
    def selected_option_rows():
        # Cached Angel One contracts must never appear as current Dhan/Yahoo option data.
        if prefs.get("source")!="Broker API" or not angel_feed.connected:
            return []
        if option_feed.get("symbol")==chain_symbol.value and option_feed.get("expiry")==expiry.value:
            return option_feed.get("rows",[])
        # A persisted strike window is historical evidence, not a fresh broker quote.
        # Do not resurrect it as current option-chain data after reconnect or restart.
        return []
    def option_metrics(kind):
        data=dhan_option_metrics
        if (data.get("symbol")!=chain_symbol.value or data.get("expiry")!=expiry.value):
            return note("Dhan option metrics unavailable for selected expiry; press Refresh selected data.")
        if kind=="PCR":
            return note("Dhan OI PCR: "+f'{data["pcr"]:.3f}'+" • UNVERIFIED • not a trading signal")
        if kind=="OI":
            return note("Dhan Max Pain: "+f'{data["max_pain"]:,.0f}'+" • UNVERIFIED • live orders OFF")
        return note("Premium flow unavailable without verified volume and transaction direction.")
    def option_chain_preview():
        # Keep the structure visible without presenting missing quotes as zero.
        headings=["CE Premium","CE OI","Strike","PE OI","PE Premium"]
        strike=str(option_strike.value or "").strip() or "—"
        rows=selected_option_rows();grouped={}
        for row in rows:grouped.setdefault(row["strike"],{})[row["side"]]=row
        def cell_value(row,key):
            val=row.get(key)
            return (f"{float(val):,.0f}" if key=="oi" else f"{float(val):,.2f}") if val is not None else "—"
        table_rows=[]
        for strike_value,sides in sorted(grouped.items()):
            ce=sides.get("CE",{});pe=sides.get("PE",{})
            times=[r.get("timestamp") for r in sides.values()]
            fresh=times and all(t is not None and 0<=datetime.now(timezone.utc).timestamp()-t<=90 for t in times)
            label=f"{strike_value:g}"+("" if fresh else " • OLD")
            table_rows.append(ft.DataRow(cells=[ft.DataCell(txt(v,12,MUTED)) for v in [cell_value(ce,"premium"),cell_value(ce,"oi"),label,cell_value(pe,"oi"),cell_value(pe,"premium")]]))
        table=ft.DataTable(
            columns=[ft.DataColumn(txt(label,12,GOLD,True)) for label in headings],
            rows=table_rows or [ft.DataRow(cells=[ft.DataCell(txt(value,13,MUTED)) for value in ["—","—",strike+" (manual)","—","—"]])],
            column_spacing=10,
            horizontal_margin=8,
        )
        return ft.Column([
            note("Underlying: "+str(chain_symbol.value)+" • "+quote_price(chain_symbol.value)),
            note("Underlying provider: "+({"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Unverified"))+" • price freshness must be verified separately. CE/PE quotes require a connected supported option-chain broker."),
            ft.Row([table],scroll=ft.ScrollMode.ALWAYS),
            note("Last available option quotes • timestamps below • not a live connection guarantee") if rows and not angel_feed.connected else note(option_feed_status[0]) if rows else note("Option chain not connected • Dhan PCR and Max Pain available after refresh; CE/PE premiums not verified."),
            note(quote_caption(chain_symbol.value)),
            note("Option quote times (IST): "+", ".join(sorted({datetime.fromtimestamp(r["timestamp"],timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M:%S") for r in rows if r.get("timestamp")}))) if rows else note("No option quote timestamps yet"),
            note(option_feed_status[0]),
            ft.ElevatedButton("Refresh selected data",on_click=lambda e:page.run_task(refresh_selected_options)),
            note("Dhan broker-listed expiry and unverified metrics only. Strike premiums unavailable; paper orders remain disabled."),
        ],horizontal_alignment=ft.CrossAxisAlignment.STRETCH,spacing=8)
    def options():
        content=[heading("Options • One scroll page"),symbol_search(chain_symbol),chain_symbol,option_expiry_choice,expiry,option_expiry_note,
                 ft.Column([option_add_symbol,ft.ElevatedButton("Add",on_click=add_option_symbol)],horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                 note("Selected: "+str(chain_symbol.value)+" • "+str(expiry.value or "expiry not set"))]
        content.extend([section('Option Chain', ft.Column([ft.Row([txt('CALL (CE)', 14, GREEN, True), txt('STRIKE', 14, GOLD, True), txt('PUT (PE)', 14, RED, True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Column([option_chain_preview(), ft.Column([option_strike, option_side],horizontal_alignment=ft.CrossAxisAlignment.STRETCH), option_qty, ft.Row([ft.ElevatedButton('BUY • Paper', on_click=lambda e: option_paper_action('BUY'), bgcolor=GREEN, color=BG), ft.ElevatedButton('SELL • Paper', on_click=lambda e: option_paper_action('SELL'), bgcolor=RED, color=BG)], wrap=True), option_paper_note, option_chart_panel()])]))])
        content.append(section('OI Analysis', option_metrics('OI')))
        content.append(section('Put Call Ratio', option_metrics('PCR')))
        content.append(section('Premium Money Flow • Volume activity only', option_metrics('Flow')))
        content.append(section('Strategy Selector', ft.Column([ft.Row([ft.ElevatedButton(n, on_click=lambda e, v=n: choose_strategy(v)) for n in ['Bull Call Spread', 'Bear Put Spread', 'Iron Condor']], wrap=True), note('Selected strategy: ' + (strategy_choice[0] or 'None')), note('Educational preview only; no orders are placed')])))
        content.extend([help_box("Options", "Every section below uses the selected symbol and expiry. CE/PE prices, OI and PCR require a verified broker feed; blank values are not zero.")])
        return content
    mode=ft.Dropdown(label="Trading mode",value=prefs["mode"],options=[ft.dropdown.Option(x,"Paper simulation" if x=="Paper" else x+" • saved preference; no live orders") for x in ["Paper","Manual","Semi-Auto","Auto"]])
    # Only Dhan is selectable in the production provider control, even with legacy saved settings.
    source=ft.Dropdown(label="Data provider",dense=True,value="Dhan",options=[ft.dropdown.Option("Dhan")])
    broker_names=["Dhan","Angel One"]
    broker=ft.Dropdown(label="Select Indian API broker",value=prefs.get("broker","Dhan") if prefs.get("broker","Dhan") in broker_names else "Dhan",options=[ft.dropdown.Option(x) for x in broker_names])
    api_url=ft.TextField(label="My BOT KING server HTTPS address (optional)",value=prefs.get("api_url",""),hint_text="https://botkingrajesh.duckdns.org")
    server_access=ft.TextField(label="Server access key (not saved)",password=True,can_reveal_password=True)
    server_trust=ft.Checkbox(label="I trust this server to receive my Angel One login",value=False)
    broker_info=ft.Text("",size=13,color=MUTED)
    broker_fields={
        "Angel One":["API Key","Client Code","MPIN","TOTP (current 6-digit code)"],
        "Dhan":[]  # Dhan credentials stay on the trusted server, never in the Android UI
    }
    default_fields=[]
    credential_inputs={}
    credential_column=ft.Column(spacing=10)
    connection_status=txt("Not connected. Live broker login is not enabled in this build.",12,MUTED)
    def update_broker_info(e=None):
        name=broker.value
        labels=broker_fields.get(name,default_fields)
        credential_inputs.clear()
        controls=[]
        for label in labels:
            secret=any(word in label.lower() for word in ["secret","mpin","totp","token","key","code"])
            field=ft.TextField(label=label,password=secret,can_reveal_password=secret)
            credential_inputs[label]=field
            controls.append(field)
        credential_column.controls=controls
        broker_info.value=(name+" • Read-only Angel One market data. Live orders OFF." if name=="Angel One" else "Dhan • server-side read-only quotes and historical candles for 51 verified NSE equities and NIFTY after Connect / Check. Timestamps unverified. Live orders OFF.")
        server_trust.label=("I trust this server to receive my Angel One login" if name=="Angel One" else "Dhan uses server-side credentials; no broker token is sent from this phone")
        connection_status.value=("Dhan: Connect / Check verifies server and NIFTY LTP, then loads watchlist quotes and queues a historical candle scan. Quote timestamps remain unverified; live orders OFF." if name=="Dhan" else "Angel One: connect to enable broker read-only market data.")
        connection_status.color=MUTED
        if e is not None:page.update()
    broker.on_change=update_broker_info
    update_broker_info()
    async def revoke_and_clear():
        try:
            await asyncio.to_thread(angel_feed.revoke)
            remote_message="Disconnected. Server session cleared."
        except FeedError:
            remote_message="Local session cleared. Server unreachable; remote session expires automatically."
        broker_retry[0]=0
        dhan_feed.disconnect()
        option_feed.clear();option_snapshots.clear()
        provider_changed(None)
        for field in credential_inputs.values():field.value=""
        server_access.value="";server_trust.value=False
        connection_status.value=remote_message+" Broker data requires connection."
        connection_status.color=GREEN
        page.update()
    def clear_broker_credentials(e):
        page.run_task(revoke_and_clear)
    def pairing_diagnostic(key):
        # Display only a short digest and length, never the secret itself.
        import hashlib
        raw=key.encode("utf-8")
        return "Key length "+str(len(raw))+" bytes • SHA256 first 12: "+hashlib.sha256(raw).hexdigest()[:12]
    async def connect_angel():
        nonlocal market_status
        if broker_connect_busy[0]:return
        if broker.value!="Angel One":
            endpoint=(api_url.value or "").strip()
            # Recheck an active in-memory session without requesting the key again.
            # Never persist the pairing key in ordinary preferences.
            existing_session=(dhan_feed.connected and
                              endpoint.rstrip("/")==dhan_feed._origin and
                              not server_access.value.strip())
            if not endpoint or (not server_access.value.strip() and not existing_session):
                connection_status.value="Dhan check requires your BOT KING HTTPS server address and server access key. No Dhan token is needed on this phone."
                connection_status.color=GOLD
                page.update();return
            pairing_key=(dhan_feed._pairing_key if existing_session else server_access.value.strip())
            try:
                from server_feed import server_origin, direct_https_opener
                import urllib.request, urllib.error, json
                origin=server_origin(endpoint)
                def check_dhan():
                    req=urllib.request.Request(origin+"/dhan/status",
                        headers={"X-BotKing-Key":pairing_key,"Accept":"application/json"},method="GET")
                    with direct_https_opener().open(req,timeout=12) as response:
                        raw=response.read(8193)
                        if len(raw)>8192:raise FeedError("Server status response too large")
                        return json.loads(raw)
                dhan_check_endpoint="/dhan/status"
                result=await asyncio.to_thread(check_dhan)
                if not isinstance(result,dict) or result.get("live_orders_enabled") is not False:
                    raise FeedError("Invalid Dhan server status")
                if result.get("reauthentication_required") is True:
                    connection_status.value="Dhan: Re-login Required • token missing or expired. Press Authorize Dhan API."
                    connection_status.color=GOLD
                elif result.get("market_data_configured") is True:
                    connection_status.value="Dhan token configured on server • checking NIFTY read-only LTP..."
                    connection_status.color=GOLD
                    page.update()
                    def check_ltp():
                        req=urllib.request.Request(origin+"/dhan/ltp",
                            data=b'{"symbol":"NIFTY"}',
                            headers={"X-BotKing-Key":pairing_key,
                                     "Content-Type":"application/json","Accept":"application/json"},
                            method="POST")
                        with direct_https_opener().open(req,timeout=15) as response:
                            raw=response.read(8193)
                            if len(raw)>8192:raise FeedError("Dhan LTP response too large")
                            return json.loads(raw)
                    live_ltp_verified=False
                    dhan_check_endpoint="/dhan/ltp"
                    try:
                        quote=await asyncio.to_thread(check_ltp)
                        if (not isinstance(quote,dict) or quote.get("source")!="dhan"
                                or quote.get("symbol")!="NIFTY" or quote.get("live_orders_enabled") is not False
                                or not isinstance(quote.get("ltp"),(int,float))
                                or isinstance(quote["ltp"],bool) or not math.isfinite(quote["ltp"]) or quote["ltp"]<=0):
                            raise FeedError("Invalid Dhan quote response")
                        dhan_feed.activate_verified(endpoint,pairing_key,quote)
                        live_ltp_verified=True
                        connection_status.value=("Dhan NIFTY LTP verified via server • "
                            +str(round(quote["ltp"],2))+" • timestamp unverified; not a live signal.")
                        connection_status.color=GREEN
                    except (FeedError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ltp_exc:
                        log_error("dhan_ltp_connect",ltp_exc)
                        # Never compound a rate limit with another upstream request.
                        if isinstance(ltp_exc, urllib.error.HTTPError) and ltp_exc.code==429:
                            raise
                        dhan_check_endpoint="/dhan/intraday"
                        # Read-only historical access can work when Dhan LTP is unavailable.
                        # Verify a real candle response before enabling it; never fake an LTP.
                        from datetime import timedelta
                        today=datetime.now(timezone(timedelta(hours=5,minutes=30))).date()
                        payload={"symbol":"RELIANCE","interval":5,
                                 "from_date":str(today-timedelta(days=5)),"to_date":str(today)}
                        def check_candles():
                            req=urllib.request.Request(origin+"/dhan/intraday",
                                data=json.dumps(payload).encode("utf-8"),
                                headers={"X-BotKing-Key":pairing_key,
                                         "Content-Type":"application/json","Accept":"application/json"},
                                method="POST")
                            with direct_https_opener().open(req,timeout=30) as response:
                                raw=response.read(2_000_001)
                                if len(raw)>2_000_000:raise FeedError("Dhan candles response too large")
                                return json.loads(raw)
                        candles=await asyncio.to_thread(check_candles)
                        dhan_feed.activate_historical_verified(endpoint,pairing_key,candles)
                        connection_status.value="Dhan historical candles verified • LIVE LTP UNAVAILABLE • read-only charts only"
                        connection_status.color=GOLD
                    source.value="Dhan";prefs["source"]="Dhan";save()
                    provider_changed(None)
                    # Verify watchlist batch independently of the login check.
                    try:
                        batch=await asyncio.to_thread(dhan_feed.batch_quotes)
                        if not batch:
                            raise FeedError("Empty Dhan batch response")
                        with dhan_batch_lock:
                            dhan_batch_cache.update(generation=provider_generation[0],
                                                    updated=time.monotonic(),quotes=batch)
                        # Keep previously valid Dhan quotes for symbols absent from
                        # a partial batch. They remain historical/unverified, not live.
                        for ticker,snapshot in batch.items():
                            if (ticker in all_watch_symbols() and snapshot.get('source')=='Dhan'
                                    and isinstance(snapshot.get('price'),(int,float))
                                    and not isinstance(snapshot.get('price'),bool)
                                    and math.isfinite(snapshot['price']) and snapshot['price']>0):
                                previous=quotes.get(ticker) or {}
                                quotes[ticker]=dict(snapshot,change=None,
                                    bars=previous.get('bars',[]) if previous.get('source')=='Dhan' else [],
                                    fetched_at=time.time())
                        failed_symbols.clear()
                        expected=len(all_watch_symbols())
                        received=sum(1 for ticker in all_watch_symbols() if
                                     (item:=batch.get(ticker)) and item.get('source')=='Dhan'
                                     and isinstance(item.get('price'),(int,float))
                                     and not isinstance(item.get('price'),bool)
                                     and math.isfinite(item['price']) and item['price']>0)
                        dhan_batch_issue[0]=(f"Partial Dhan batch: {received}/{expected} symbols returned"
                                             if received<expected else None)
                        market_status=('Dhan • '+str(received)+'/'+str(expected)+
                                       ' equity LTP quotes returned; timestamps unverified'+
                                       (' • PARTIAL' if dhan_batch_issue[0] else ''))
                        if current[0] in (0,4):request_view_refresh(current[0])
                    except Exception as exc:
                        log_error('dhan_batch_after_connect',exc)
                        with dhan_batch_lock:
                            dhan_batch_cache.update(generation=None,updated=0.0,quotes={})
                        # A failed refresh must not erase the last valid Dhan quote.
                        # The error status above makes refresh failure explicit.
                        dhan_batch_issue[0]=safe_error(exc)
                        market_status='Dhan connected; watchlist batch failed: '+safe_error(exc)
                    if market_status.startswith("Dhan connected; watchlist batch failed"):
                        connection_status.value=(("Dhan LTP verified; batch quotes unavailable • historical scan queued"
                                                  if live_ltp_verified else
                                                  "Dhan historical-only connection • LIVE LTP UNAVAILABLE • "
                                                  "watchlist prices unavailable; historical scan queued"))
                        connection_status.color=GOLD
                    else:
                        connection_status.value=("Dhan connected • "+str(received)+"/"+str(expected)+
                            " equity LTP quotes returned • timestamps unverified"+
                            (" • PARTIAL" if dhan_batch_issue[0] else ""))
                        connection_status.color=GOLD if dhan_batch_issue[0] else GREEN
                    # Historical scan must run even if the independent LTP batch fails.
                    provider_generation[0]+=1
                    with dhan_batch_lock:
                        dhan_batch_cache["generation"]=provider_generation[0]
                    # Start the independent watchlist poll immediately after a successful
                    # Dhan connection; do not wait for the next 30-second timer tick.
                    if app_active[0] and dhan_feed.connected:
                        page.run_task(refresh_watch_batch)
                    scan_progress.update(checked=0,total=len(watch_symbols),valid=0,
                        failed=0,cached=0,state="Dhan historical scan queued; LTP independently checked")
                else:
                    connection_status.value=("Dhan Connected (OAuth), but market-data token is unavailable."
                        if result.get("authenticated") else
                        "Dhan: Not Connected • press Authorize Dhan API to sign in.")
                    connection_status.color=GOLD
            except urllib.error.HTTPError as exc:
                log_error("dhan_connect_http",exc)
                code=exc.code
                if code==403:
                    detail="Dhan /status HTTP 403 • "+pairing_diagnostic(pairing_key)+". Compare with Oracle key fingerprint."
                elif code==429:
                    detail=f"Dhan {dhan_check_endpoint} HTTP 429 • rate limited; wait before retrying. No extra fallback request sent after LTP 429."
                elif code==404:
                    detail="Dhan endpoint not found (HTTP 404). Check HTTPS proxy routing."
                elif code in (502,503,504):
                    detail=f"Dhan upstream/backend error (HTTP {code}). Check server logs and Dhan token."
                else:
                    detail=f"Dhan server returned HTTP {code}. Check backend logs."
                connection_status.value=detail
                connection_status.color=RED
            except (urllib.error.URLError,TimeoutError) as exc:
                log_error("dhan_status_network",exc)
                connection_status.value="Dhan network/TLS connection failed or timed out. Check phone internet, HTTPS certificate and server URL."
                connection_status.color=RED
            except Exception as exc:
                log_error("dhan_status",exc)
                connection_status.value="Dhan check failed ("+type(exc).__name__+"). Check server response format and app logs."
                connection_status.color=RED
            finally:
                server_access.value=""
            page.update();return
        endpoint=(api_url.value or "").strip()
        if endpoint and not server_trust.value:
            connection_status.value="Confirm that you trust this server before sending your broker login."
            page.update();return
        broker_connect_busy[0]=True
        connection_status.value="Connecting to Angel One read-only market data"+(" through your server..." if endpoint else " directly...")
        page.update()
        values=[credential_inputs[label].value or "" for label in broker_fields["Angel One"]]
        try:
            await asyncio.to_thread(angel_feed.connect,*values,endpoint,server_access.value or "")
            for field in credential_inputs.values():field.value=""
            server_access.value=""
            broker_retry[0]=0
            source.value=prefs.get("source","Dhan");save()
            provider_changed(None)
            connection_status.value="Angel One connected"+(" through your server" if endpoint else " directly")+" • market data only • reconnect after session expiry or restart"
            connection_status.color=GREEN
            page.run_task(refresh_selected_options)
        except FeedError as exc:
            log_error("broker_login",exc)
            # FeedError messages are curated by the transport; never show raw
            # HTTP response bodies, broker tokens or unhandled exception text.
            connection_status.value="Connection failed: "+str(exc)+" • Broker data unavailable."
            connection_status.color=RED
        except Exception as exc:
            log_error("broker_login",exc)
            connection_status.value="Connection failed unexpectedly. Check app diagnostics; broker data unavailable."
            connection_status.color=RED
        finally:
            values.clear()
            broker_connect_busy[0]=False
        page.update()
    async def start_dhan_authorization():
        if broker.value!="Dhan":
            connection_status.value="Select Dhan as the broker before authorization."
            page.update();return
        endpoint=(api_url.value or "").strip()
        pairing_key=(server_access.value or "").strip()
        if not endpoint or not pairing_key:
            connection_status.value="Enter the BOT KING HTTPS server URL and Server Access Key first."
            connection_status.color=GOLD
            page.update();return
        try:
            from server_feed import server_origin, direct_https_opener
            import urllib.request, urllib.error, json
            from urllib.parse import urlsplit
            origin=server_origin(endpoint)
            # Prefer the already-provisioned Oracle Dhan token. A second browser
            # consent is unnecessary and can fail independently of market data.
            def check_existing_token():
                req=urllib.request.Request(origin+"/dhan/status",
                    headers={"X-BotKing-Key":pairing_key,"Accept":"application/json"},method="GET")
                with direct_https_opener().open(req,timeout=12) as response:
                    raw=response.read(8193)
                    if len(raw)>8192:raise FeedError("Dhan status response too large")
                    return json.loads(raw)
            existing=await asyncio.to_thread(check_existing_token)
            if not isinstance(existing,dict) or existing.get("live_orders_enabled") is not False:
                raise FeedError("Invalid Dhan status response")
            # Status authorization succeeded. Any later HTTP 403 belongs to
            # /dhan/start, not /dhan/status; report the failing stage precisely.
            # Explicit Dhan authorization must always request fresh consent.
            # The server's market_data_configured flag only means a token file
            # exists; an expired/revoked token can still set it to True.
            # Connect / Check remains a separate, quote-verified action.
            def request_consent():
                req=urllib.request.Request(origin+"/dhan/start",data=b"",
                    headers={"X-BotKing-Key":pairing_key,"Accept":"application/json"},method="POST")
                with direct_https_opener().open(req,timeout=15) as response:
                    raw=response.read(8193)
                    if len(raw)>8192:raise FeedError("Dhan consent response too large")
                    return json.loads(raw)
            try:
                result=await asyncio.to_thread(request_consent)
            except urllib.error.HTTPError as exc:
                if exc.code == 403:
                    raise FeedError("Dhan /start HTTP 403 • "+pairing_diagnostic(pairing_key)+". Compare with Oracle key fingerprint.") from None
                raise
            login_url=result.get("login_url","") if isinstance(result,dict) else ""
            parsed=urlsplit(login_url)
            if (parsed.scheme!="https" or parsed.hostname!="auth.dhan.co"
                    or parsed.username or parsed.password or parsed.port):
                raise FeedError("Unexpected Dhan authorization URL")
            connection_status.value="Dhan authorization opened in browser. Complete consent, then return and press Connect / Check."
            connection_status.color=GOLD
            page.update()
            page.launch_url(login_url)
        except urllib.error.HTTPError as exc:
            connection_status.value=("Dhan /status HTTP 403 • "+pairing_diagnostic(pairing_key)+". Compare with Oracle key fingerprint." if exc.code==403 else
                "Dhan authorization could not start (HTTP "+str(exc.code)+"). Check server Dhan credentials and pending login.")
            connection_status.color=RED
            page.update()
        except FeedError as exc:
            log_error("dhan_oauth_start",exc)
            connection_status.value=str(exc) if "Dhan /start HTTP 403" in str(exc) else "Dhan authorization could not start. Check HTTPS connection and server configuration."
            connection_status.color=RED
            page.update()
        except Exception as exc:
            log_error("dhan_oauth_start",exc)
            connection_status.value="Dhan authorization could not start. Check HTTPS connection and server configuration."
            connection_status.color=RED
            page.update()
    def open_dhan_authorization(e):
        page.run_task(start_dhan_authorization)
    def explain_broker_connection(e):
        page.run_task(connect_angel)

    # Trading Bot controls: offline calculation and paper-only order simulation.
    bot_segment=ft.Dropdown(label="Segment",value=prefs.get("bot_segment","Options"),options=[ft.dropdown.Option("Options"),ft.dropdown.Option("Cash")])
    bot_side=ft.Dropdown(label="Plan side",value=prefs.get("bot_side","BUY"),options=[ft.dropdown.Option("BUY"),ft.dropdown.Option("SELL")])
    cash_max_quantity=ft.TextField(label="Maximum total cash shares",value=str(prefs.get("cash_max_quantity",10000)))
    cash_quantity=ft.TextField(label="Cash shares",value=str(prefs.get("cash_quantity",1)),keyboard_type=ft.KeyboardType.NUMBER)
    manual_contract_confirmed=ft.Checkbox(label="I verified manual contract, lot size and premium • Paper only",value=bool(prefs.get("manual_contract_confirmed",False)))
    paper_capital=ft.TextField(label="Paper capital (INR)",value=str(prefs.get("paper_capital",100000)))
    paper_notional_limit=ft.TextField(label="Max paper notional per position (not margin)",value=str(prefs.get("paper_notional_limit",100000)))
    paper_trade_risk=ft.TextField(label="Max planned risk per trade (INR)",value=str(prefs.get("paper_trade_risk",1000)))
    paper_risk_pct=ft.TextField(label="Max planned risk per trade (%)",value=str(prefs.get("paper_risk_pct",1)))
    paper_exit_price=ft.TextField(label="Manual exit price • optional; blank means unknown",value="")
    paper_exit_fees=ft.TextField(label="Paper charges (INR) • 0 excludes charges",value="0")
    paper_max_additions=ft.TextField(label="Maximum paper additions",value=str(prefs.get("paper_max_additions",1)))
    paper_add_units=ft.TextField(label="Lots / shares per addition",value=str(prefs.get("paper_add_units",1)))
    paper_trail_pct=ft.TextField(label="Paper trailing price distance (%)",value=str(prefs.get("paper_trail_pct",2)))
    paper_partial_trigger=ft.TextField(label="Paper partial profit trigger (%)",value=str(prefs.get("paper_partial_trigger",2)))
    paper_partial_pct=ft.TextField(label="Paper partial quantity (%)",value=str(prefs.get("paper_partial_pct",50)))
    paper_reentry_after_sl=ft.Checkbox(label="Allow paper re-entry after stop-loss",value=bool(prefs.get("paper_reentry_after_sl",False)))
    paper_bot_state=["Stopped"];paper_last_exit={};paper_exit_reason=["Manual paper exit"]
    paper_state_status=txt("Paper bot stopped • no live orders • manual marks required",12,GOLD)

    bot_symbol=ft.Dropdown(label="Instrument",value=prefs.get("bot_symbol","NIFTY"),options=[ft.dropdown.Option(x) for x in selection_symbols()+["Custom"]])
    bot_custom=ft.TextField(label="Custom symbol (optional)",value=prefs.get("bot_custom",""))
    bot_type=ft.Dropdown(label="Option type",value=prefs.get("bot_type","CE"),options=[ft.dropdown.Option(x) for x in ["CE","PE"]])
    bot_strike=ft.TextField(label="Strike price",value=str(prefs.get("bot_strike","23400")),keyboard_type=ft.KeyboardType.NUMBER)
    bot_expiry=ft.TextField(label="Expiry (YYYY-MM-DD)",value=prefs.get("bot_expiry",""),hint_text="Select contract expiry manually")
    bot_lots=ft.Dropdown(label="Number of lots",value=str(prefs.get("bot_lots",1)),options=[ft.dropdown.Option(str(i),f"{i} Lot"+("s" if i>1 else "")) for i in range(1,51)])
    # Calendar suggestions are only previews, not verified exchange contracts.
    def preview_expiries(instrument):
        # Same calendar-preview provider as Options; never a verified listed contract.
        return [d.isoformat() for d in option_dates(instrument)]
    bot_expiry_mode=ft.Dropdown(label="Expiry selection",value="Nearest (preview)",options=[ft.dropdown.Option(x) for x in ["Nearest (preview)","Next (preview)","Manual"]])
    expiry_warning=ft.Text("Calendar estimate only. Holiday shifts and exchange-listed expiries are not verified; paper mode only.",size=12,color=GOLD)
    def update_expiry(e=None):
        instrument=(bot_custom.value or "").strip().upper() if bot_symbol.value=="Custom" else bot_symbol.value
        previous=prefs.get("bot_contract_symbol",instrument)
        if e is not None and previous!=instrument:
            for control,key in ((bot_strike,"bot_strike"),(bot_premium,"bot_premium"),(bot_lot_size,"bot_lot_size")):
                control.value="";prefs[key]=""
            manual_contract_confirmed.value=False;prefs["manual_contract_confirmed"]=False
            bot_preview.value="Symbol changed. Enter this contract's strike, premium and units per lot."
        prefs["bot_contract_symbol"]=instrument
        choices=preview_expiries(instrument)
        selected=choices[1] if bot_expiry_mode.value=="Next (preview)" and len(choices)>1 else (choices[0] if choices else "")
        if bot_expiry_mode.value!="Manual":
            bot_expiry.value=selected
            prefs["bot_expiry"]=selected
            prefs["bot_expiry_mode"]=bot_expiry_mode.value
            prefs["bot_symbol"]=bot_symbol.value
            save()
            bot_expiry.read_only=True
        else:
            bot_expiry.read_only=False
        if e is not None:page.update()
    bot_expiry_mode.on_change=update_expiry
    bot_symbol.on_change=update_expiry
    bot_custom.on_change=update_expiry
    bot_lot_size=ft.TextField(label="Units per lot (verify with exchange)",value=str(prefs.get("bot_lot_size",1)),keyboard_type=ft.KeyboardType.NUMBER)
    bot_premium=ft.TextField(label="Entry premium (INR)",value=str(prefs.get("bot_premium",80)),keyboard_type=ft.KeyboardType.NUMBER)
    bot_trailing=ft.Switch(label="Trailing stop • paper manual ticks",value=bool(prefs.get("bot_trailing",False)),active_color=GOLD)
    # Saved strategy preferences only: no unattended execution or live orders.
    auto_entry=ft.Switch(label="Entry when Paper Start is pressed",value=bool(prefs.get("auto_entry",False)),active_color=GOLD)
    auto_reentry=ft.Switch(label="Paper re-entry on a new manual tick",value=bool(prefs.get("auto_reentry",False)),active_color=GOLD)
    buy_dip=ft.Switch(label="Paper averaging on manual ticks • BUY only",value=bool(prefs.get("buy_dip",False)),active_color=GOLD)
    partial_profit=ft.Switch(label="Paper partial profit on manual ticks",value=bool(prefs.get("partial_profit",False)),active_color=GOLD)
    max_total_lots=ft.Dropdown(label="Maximum total lots",value=str(prefs.get("max_total_lots",2)),options=[ft.dropdown.Option(str(i)) for i in range(1,51)])
    dip_step=ft.TextField(label="Minimum dip before adding (%)",value=str(prefs.get("dip_step",5)),keyboard_type=ft.KeyboardType.NUMBER)
    max_daily_loss=ft.TextField(label="Daily planned-risk budget (paper INR)",value=str(prefs.get("max_daily_loss",1000)),keyboard_type=ft.KeyboardType.NUMBER)
    cooldown=ft.Dropdown(label="Re-entry cooldown (minutes)",value=str(prefs.get("cooldown",15)),options=[ft.dropdown.Option(str(i)) for i in [5,10,15,30,60]])
    squareoff=ft.Dropdown(label="Paper square-off time",value=str(prefs.get("squareoff","15:15")),options=[ft.dropdown.Option(x) for x in ["15:00","15:10","15:15","15:20","15:25"]])
    emergency_stop=ft.Switch(label="Emergency stop (paper)",value=bool(prefs.get("emergency_stop",False)),active_color=RED)
    protection_mode=ft.Dropdown(label="Position protection • PAPER ONLY",value=prefs.get("protection_mode","Manual"),options=[ft.dropdown.Option(x) for x in ["Manual","Assisted","Auto (Paper)"]])
    protection_enabled=ft.Switch(label="Enable paper protection demonstration",value=bool(prefs.get("protection_enabled",False)),active_color=GOLD)
    protection_loss=ft.TextField(label="Paper alert / exit loss (INR)",value=str(prefs.get("protection_loss",100)))
    protection_profit=ft.TextField(label="Paper profit target (INR)",value=str(prefs.get("protection_profit",200)))
    protection_trail=ft.TextField(label="Profit giveback from peak (%)",value=str(prefs.get("protection_trail",25)))
    protection_timeout=ft.TextField(label="Assisted response timeout (seconds)",value=str(prefs.get("protection_timeout",30)))
    protection_no_reply=ft.Checkbox(label="Allow PAPER exit after timeout if I do not respond",value=bool(prefs.get("protection_no_reply",False)))
    paper_mark=ft.TextField(label="Current PAPER price • manually supplied",hint_text="No live option feed is connected")
    protection_status=txt("Live position protection is NOT connected. Paper demonstration requires a manual current premium.",12,GOLD)
    protection_sample={};protection_pending={};protection_peak=[0.0]
    bot_preview=txt("Enter contract and tap Calculate.",13,MUTED)
    bot_trade_status=txt("Saved paper position: "+str((prefs.get("bot_position") or {}).get("contract") or "FLAT"),12,MUTED)
    bot_position=dict(prefs.get("bot_position") or {"side":None,"entry":None,"quantity":0,"contract":None})
    bot_expiry_mode.value=prefs.get("bot_expiry_mode","Nearest (preview)")
    update_expiry()
    def bot_values():
        p=finite(bot_premium.value,"Entry",.000001);st=finite(sl.value,"Stop",.000001);tg=finite(target.value,"Target",.000001)
        if not 0<st<100 or not 0<tg<=1000:raise ValueError("Check stop loss and target")
        sym=(bot_custom.value or "").strip().upper() if bot_symbol.value=="Custom" else bot_symbol.value
        if not sym or not all(c.isalnum() or c in "-&." for c in sym):raise ValueError("Enter a valid symbol")
        if bot_segment.value=="Cash":
            if sym in ("NIFTY","BANKNIFTY","FINNIFTY","SENSEX"):raise ValueError("An index is not a cash share; choose a stock")
            qty=int(cash_quantity.value)
            if qty<1:raise ValueError("Cash quantity must be a positive integer")
            contract=sym+" CASH"
            if qty>int(cash_max_quantity.value):raise ValueError("Maximum total shares exceeded")
        else:
            lots=int(bot_lots.value);unit=int(bot_lot_size.value);strike=finite(bot_strike.value,"Strike",.000001)
            if not (1<=lots<=50 and 1<=unit<=100000):raise ValueError("Check lots and units per lot")
            if lots>int(max_total_lots.value):raise ValueError("Maximum total lots must cover the selected entry lots.")
            if not bot_expiry.value:raise ValueError("Set contract expiry")
            validate_expiry(bot_expiry.value,datetime.now(timezone(timedelta(hours=5,minutes=30))).date())
            contract=f"{sym} {strike:g} {bot_type.value} {bot_expiry.value}"
            qty=lots*unit
        return p,st,tg,qty,contract
    def check_trade_risk(price,qty,stop):
        return risk_check(price,qty,stop,paper_capital.value,paper_notional_limit.value,paper_trade_risk.value,paper_risk_pct.value)
    def calculate_bot(e=None):
        try:
            p,st,tg,qty,contract=bot_values();stop,take=levels(bot_side.value,p,st,tg)
            planned=check_trade_risk(p,qty,stop)
            quantity=(f"{bot_lots.value} lots × {bot_lot_size.value} units = {qty}" if bot_segment.value=="Options" else str(qty)+" shares")
            bot_preview.value=f"MANUAL EXAMPLE • unverified contract / premium / lot size\nPAPER {bot_side.value} {contract} | Qty {qty} ({quantity}) | Entry INR {p:.2f} | SL INR {stop:.2f} | Target INR {take:.2f} | Notional INR {p*qty:,.2f} | Planned stop-risk INR {planned:,.2f} | Risk:reward 1:{tg/st:.2f}. Not broker margin; charges/slippage/gaps excluded. Short-option loss can exceed planned risk."
            bot_preview.color=GREEN
        except (ValueError,TypeError,OverflowError) as exc:bot_preview.value="Invalid input: "+str(exc);bot_preview.color=RED
        page.update()
    def paper_day():
        return datetime.now(timezone(timedelta(hours=5,minutes=30))).date().isoformat()
    def paper_risk_ledger():
        today=paper_day()
        ledgers=prefs.setdefault("paper_daily_limits",{})
        if today not in ledgers:
            # Preserve accepted entries from older builds during this day's migration.
            accepted=[]
            for event in prefs.get("bot_paper_events",[]):
                try:
                    when=datetime.fromisoformat(event["time"])
                    if when.tzinfo is None:when=when.replace(tzinfo=timezone.utc)
                    if (when.astimezone(timezone(timedelta(hours=5,minutes=30))).date().isoformat()==today
                            and event.get("status","").startswith("SIMULATED ")
                            and event.get("action") in ("BUY","SELL")):
                        accepted.append(event)
                except (KeyError,ValueError,TypeError):continue
            used=0.0
            for event in accepted:
                position=event.get("position") or {}
                try:used+=float(position["entry"])*int(position["quantity"])*float(position.get("stop_loss_pct",2))/100
                except (KeyError,ValueError,TypeError):pass
            ledgers[today]={"entries":len(accepted),"planned_risk_used":used}
        for day in sorted(ledgers)[:-35]:del ledgers[day]
        return ledgers[today]
    def bot_paper_action(side):
        with trade_lock:
            try:bot_paper_action_locked(side)
            except (ValueError,TypeError,OverflowError) as exc:
                bot_trade_status.value="Paper action blocked: "+str(exc);bot_trade_status.color=RED;page.update()
    def bot_paper_action_locked(side):
        before=dict(bot_position)
        if mode.value!="Paper":
            bot_trade_status.value="Live orders disabled. Select Paper mode for simulation."
            bot_trade_status.color=RED
        elif side=="EXIT":
            if bot_position["side"]:
                valid_mark=(protection_sample.get("position_id")==bot_position.get("position_id") and datetime.now().timestamp()-protection_sample.get("time",0)<=60)
                mark=finite(paper_exit_price.value,"Exit") if str(paper_exit_price.value or "").strip() else protection_sample.get("mark") if valid_mark else None
                fees=finite(paper_exit_fees.value or 0,"Charges")
                if mark is not None:
                    gross,net=paper_pnl(bot_position["side"],bot_position["entry"],mark,bot_position["quantity"],fees)
                    protection_sample.update(position_id=bot_position.get("position_id"),mark=mark,pnl=net,gross_pnl=gross,fees=fees,time=datetime.now().timestamp())
                    ledger=paper_risk_ledger();ledger["realized_loss"]=float(ledger.get("realized_loss",0))+max(0,-net)
                else:
                    protection_sample.clear()
                    ledger=paper_risk_ledger();ledger["unknown_exits"]=int(ledger.get("unknown_exits",0))+1
                paper_last_exit.update(position=dict(bot_position),time=datetime.now().timestamp(),reason=paper_exit_reason[0],known=mark is not None)
                bot_trade_status.value=paper_exit_reason[0]+(f" • Manual exit {mark:.2f} • net PAPER P&L {protection_sample['pnl']:.2f}" if mark is not None else " • exit price/P&L unknown")
                paper_exit_reason[0]="Manual paper exit"
                bot_position.update(side=None,entry=None,quantity=0,contract=None)
                bot_trade_status.color=GREEN
            else:
                bot_trade_status.value="No paper option position to exit."
                bot_trade_status.color=MUTED
        elif emergency_stop.value:
            bot_trade_status.value="Emergency stop active. New paper entries blocked."
            bot_trade_status.color=RED
        elif bot_position["side"]:
            bot_trade_status.value="Exit the existing paper position before another entry."
            bot_trade_status.color=RED
        else:
            try:
                p,st,tg,qty,contract=bot_values()
                if not manual_contract_confirmed.value:raise ValueError("Confirm manual contract, lot size and premium before paper entry")
                validate_field(limit,"max_trades",limit.value)
                validate_field(max_daily_loss,"max_daily_loss",max_daily_loss.value)
                ledger=paper_risk_ledger()
                if int(ledger.get("unknown_exits",0))>0:
                    raise ValueError("Unknown paper exit P&L: reconcile daily risk before another entry")
                if int(ledger["entries"])>=int(limit.value):
                    raise ValueError("Daily paper entry limit reached. EXIT remains available.")
                stop,take=levels(side,p,st,tg)
                planned_risk=check_trade_risk(p,qty,stop)
                if float(ledger.get("realized_loss",0))>=float(max_daily_loss.value):raise ValueError("Daily realized paper loss limit reached")
                remaining=float(max_daily_loss.value)-float(ledger["planned_risk_used"])
                if planned_risk>remaining+1e-9:
                    raise ValueError("Daily paper planned-risk budget exceeded. This is not actual loss accounting.")
                ledger["entries"]+=1
                ledger["planned_risk_used"]+=planned_risk
                bot_position.update(side=side,entry=p,quantity=qty,contract=contract,stop_loss_pct=st,target_pct=tg,position_id=__import__("uuid").uuid4().hex,
                    stop_price=stop,target_price=take,unit_size=1 if bot_segment.value=="Cash" else int(bot_lot_size.value),segment=bot_segment.value,additions=0,last_add_price=p,partial_done=False,best_mark=p)
                paper_exit_price.value=""
                protection_sample.clear();protection_pending.clear();protection_peak[0]=0
                bot_trade_status.value=f"SIMULATED {side} {contract} | {qty} units @ INR {p:.2f} | SL INR {stop:.2f} | Target INR {take:.2f}. No real order."
                bot_trade_status.color=GREEN
            except (ValueError,TypeError,OverflowError) as exc:
                bot_trade_status.value="Paper entry blocked: "+str(exc)
                bot_trade_status.color=RED
        if before.get("side")!=bot_position.get("side"):
            journal=prefs.setdefault("paper_journal",[])
            journal.append({"time":datetime.now(timezone.utc).isoformat(timespec="seconds"),"event":side,"contract":(before if side=="EXIT" else bot_position).get("contract"),"quantity":(before if side=="EXIT" else bot_position).get("quantity"),"entry":(before if side=="EXIT" else bot_position).get("entry"),"reason":bot_trade_status.value,"exit_price":protection_sample.get("mark") if side=="EXIT" else None,"charges":protection_sample.get("fees") if side=="EXIT" else None,"paper_pnl":protection_sample.get("pnl") if side=="EXIT" and protection_sample.get("position_id")==before.get("position_id") and datetime.now().timestamp()-protection_sample.get("time",0)<=60 else None})
            del journal[:-200]
            if side=="EXIT":protection_pending.clear();protection_sample.clear();protection_peak[0]=0;paper_exit_fees.value="0"
        prefs["bot_position"]=dict(bot_position)
        events=prefs.setdefault("bot_paper_events",[])
        events.append({"time":datetime.now(timezone.utc).isoformat(timespec="seconds"),"action":side,"position":dict(bot_position),"status":bot_trade_status.value})
        del events[:-200]
        if not save():bot_trade_status.value+=" • WARNING: position could not be saved"
        page.update()

    sl=ft.TextField(label="Stop loss %",value=str(prefs["stop_loss"]),keyboard_type=ft.KeyboardType.NUMBER)
    target=ft.TextField(label="Target %",value=str(prefs["target"]),keyboard_type=ft.KeyboardType.NUMBER)
    limit=ft.TextField(label="Max trades per day",value=str(prefs["max_trades"]),keyboard_type=ft.KeyboardType.NUMBER)
    conf=ft.Slider(min=70,max=85,divisions=15,value=prefs["confidence"],label="{value}%")
    status=txt("Broker orders disabled. Paper Buy/Sell is simulated.",12,RED)
    paper_position={"side":None,"entry":None,"symbol":None}
    paper_status=txt("Paper position: FLAT",12,MUTED)
    def paper_trade(side):
        if mode.value!="Paper":
            paper_status.value="Switch to Paper mode for simulated Buy / Sell."
            paper_status.color=RED
        elif side=="EXIT":
            if paper_position["side"]:
                paper_status.value="Paper position closed (simulation only)."
                paper_position.update(side=None,entry=None,symbol=None)
                paper_status.color=GREEN
            else:paper_status.value="No paper position to exit."
        elif paper_position["side"]:
            paper_status.value="Exit the existing quick paper position before another entry."
            paper_status.color=RED
        elif emergency_stop.value:
            paper_status.value="Emergency stop active. Quick paper entries blocked."
            paper_status.color=RED
        else:
            sym=symbol.value
            q=quotes.get(sym)
            expected_source={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            stamp=q.get("quote_timestamp") if q else None
            try:
                age=time.time()-float(stamp)
                quote_fresh=0<=age<=90
            except (TypeError,ValueError,OverflowError):
                quote_fresh=False
            try:
                paper_price=finite(q.get("price"),"Paper quote",.000001) if q else None
            except (ValueError,TypeError,OverflowError):
                paper_price=None
            if (paper_price is None or q.get("source")!=expected_source
                    or q.get("cached") or not quote_fresh):
                paper_status.value="Cannot simulate entry: positive current-provider quote with recent timestamp unavailable; exchange verification not implied."
                paper_status.color=RED
            else:
                paper_position.update(side=side,entry=paper_price,symbol=sym)
                paper_status.value=f"Paper {side} {sym} @ {paper_price:,.2f} • SL {sl.value}% • Target {target.value}% (not an actual order)"
                paper_status.color=GREEN
        page.update()

    field_bindings=[]
    undoing=[False]
    def validate_field(control,key,value):
        import math
        ints={"max_trades":(1,50),"bot_lots":(1,50),"bot_lot_size":(1,100000),"max_total_lots":(1,50),"cooldown":(1,1440),"option_qty":(1,100000),"confidence":(70,85),"protection_timeout":(5,300)}
        floats={"stop_loss":(0,99.99),"target":(0,100),"bot_premium":(0,1e9),"bot_strike":(0,1e9),"dip_step":(0,100),"max_daily_loss":(0,1e12),"scanner_min":(-1e-9,1e9),"scanner_max":(0,1e9),"protection_loss":(0,1e9),"protection_profit":(0,1e9),"protection_trail":(0,100)}
        ints.update({"cash_quantity":(1,1000000),"cash_max_quantity":(1,1000000),"paper_max_additions":(0,20),"paper_add_units":(1,10000)})
        floats.update({"paper_capital":(0,1e12),"paper_notional_limit":(0,1e12),"paper_trade_risk":(0,1e12),"paper_risk_pct":(0,100),"paper_trail_pct":(0,99.99),"paper_partial_trigger":(0,100),"paper_partial_pct":(0,99.99)})
        if key in ints:
            value=int(value);lo,hi=ints[key]
            if not lo<=value<=hi:raise ValueError(f"Enter {lo}–{hi}")
        elif key in floats:
            value=float(value);lo,hi=floats[key]
            if not math.isfinite(value) or not lo<value<=hi:raise ValueError(f"Enter a number above {max(0,lo):g} and up to {hi:g}")
        elif key in ("bot_expiry","option_expiry") and value:
            datetime.strptime(value.strip(),"%Y-%m-%d")
        if isinstance(control,ft.TextField):control.error_text=None
        return value
    def save_control(control,key):
        try:
            value=validate_field(control,key,control.value)
            old=prefs.get(key)
            prefs[key]=value
            if old!=value and key!="api_url" and not undoing[0]:
                history=prefs.setdefault("setting_changes",[])
                history.append({"time":datetime.now(timezone.utc).isoformat(timespec="seconds"),"key":key,"before":old,"after":value})
                del history[:-50]
            return True
        except (ValueError,TypeError,OverflowError) as exc:
            if isinstance(control,ft.TextField):control.error_text=str(exc)
            return False
    def save_page(page_id):
        def belongs(key):
            if page_id==1:return key.startswith("option_")
            if page_id==3:return key.startswith("scanner_")
            if page_id==2:return not key.startswith(("option_","scanner_"))
            return False
        invalid=[key for control,key in field_bindings if belongs(key) and not save_control(control,key)]
        persisted=save()
        page_save_status[page_id].value=("Saved on this device" if not invalid else "Valid fields saved; fix: "+", ".join(invalid)) if persisted else "Save failed"
        page_save_status[page_id].color=GOLD if invalid else GREEN if persisted else RED
        if page_id==2:status.value=page_save_status[page_id].value;status.color=page_save_status[page_id].color
        page.update()
    def save_footer(page_id):
        return ft.Column([ft.ElevatedButton("Save changes",on_click=lambda e:save_page(page_id),bgcolor=GOLD,color=BG),page_save_status[page_id]],horizontal_alignment=ft.CrossAxisAlignment.STRETCH,spacing=4)
    def save_settings(_):
        return save_page(2)
    def legacy_save_settings(_):
        invalid=[key for control,key in field_bindings if not save_control(control,key)]
        persisted=save()
        status.value=("Valid fields saved; fix highlighted fields: "+", ".join(invalid) if invalid else "Settings saved on device.") if persisted else "Save failed — device storage unavailable"
        status.color=GOLD if invalid else GREEN if persisted else RED
        page.update()
    # Keep the initialized broker selector consistent; do not silently select Angel One.
    broker.value=prefs.get("broker","Dhan") if prefs.get("broker","Dhan") in broker_names else "Dhan"
    settings_tab=["Trading Bot"]
    def choose_settings_tab(v):
        settings_tab[0]=v
        select(2)
    def help_box(title,message):
        return ft.ExpansionTile(title=txt("ⓘ "+title+" help",13,GOLD),controls=[note(message)])
    def check_paper_protection(e=None):
        import math
        try:
            if not protection_enabled.value:raise ValueError("Paper protection is OFF")
            if mode.value!="Paper" or not bot_position.get("side"):raise ValueError("Open a paper position in Paper mode first")
            for control,key in [(protection_loss,"protection_loss"),(protection_profit,"protection_profit"),(protection_trail,"protection_trail"),(protection_timeout,"protection_timeout")]:validate_field(control,key,control.value)
            mark=float(paper_mark.value)
            if not math.isfinite(mark) or mark<0:raise ValueError("Enter a finite non-negative paper premium")
            pnl=(mark-float(bot_position["entry"]))*int(bot_position["quantity"])*(1 if bot_position["side"]=="BUY" else -1)
            protection_peak[0]=max(protection_peak[0],pnl)
            protection_sample.update(position_id=bot_position.get("position_id"),pnl=pnl,mark=mark,time=datetime.now().timestamp())
            triggered=pnl<=-float(protection_loss.value) or pnl>=float(protection_profit.value) or (protection_peak[0]>0 and pnl<=protection_peak[0]*(1-float(protection_trail.value)/100))
            protection_status.value="Manual PAPER mark: P&L INR "+format(pnl,",.2f")+(" • protection threshold reached" if triggered else " • within configured limits")
            if triggered:
                if protection_mode.value=="Auto (Paper)":bot_paper_action("EXIT");protection_status.value+=" • PAPER position exited; no broker order sent"
                elif protection_mode.value=="Assisted":
                    protection_pending.update(position_id=bot_position.get("position_id"),deadline=datetime.now().timestamp()+int(protection_timeout.value))
                    protection_status.value+=" • confirm paper exit; no-response exit requires the separate permission checkbox"
            else:protection_pending.clear()
        except (ValueError,TypeError,KeyError,OverflowError) as exc:protection_status.value="Paper check: "+str(exc)
        page.update()
    async def protection_clock():
        while True:
            await asyncio.sleep(1)
            if not (protection_pending and protection_enabled.value and protection_mode.value=="Assisted" and protection_no_reply.value
                    and mode.value=="Paper" and datetime.now().timestamp()>=protection_pending["deadline"]):continue
            if (protection_pending.get("position_id")!=bot_position.get("position_id") or protection_sample.get("position_id")!=bot_position.get("position_id")):
                protection_pending.clear();continue
            if datetime.now().timestamp()-protection_sample.get("time",0)>60:
                protection_pending.clear()
                protection_status.value="Timeout reached, but manual mark is stale — PAPER auto exit blocked. Supply a current mark or confirm exit manually."
            else:
                bot_paper_action("EXIT")
                protection_status.value="Assisted timeout • PAPER position exited using last manual mark; no live order"
            page.update()
    def paper_run(action):
        if action=="Start":
            try:
                if mode.value!="Paper":raise ValueError("Select Paper mode")
                if emergency_stop.value:raise ValueError("Emergency stop is active")
                bot_values()
                if not manual_contract_confirmed.value:raise ValueError("Confirm manual contract details")
                paper_bot_state[0]="Running"
                if auto_entry.value and not bot_position.get("side"):bot_paper_action(bot_side.value)
            except (ValueError,TypeError) as exc:paper_state_status.value="Paper Start blocked: "+str(exc);page.update();return
        else:paper_bot_state[0]="Paused" if action=="Pause" else "Stopped"
        paper_state_status.value="Paper bot: "+paper_bot_state[0]+" • evaluates only new manual ticks • no live orders"
        save();page.update()
    def paper_tick(e=None):
        with trade_lock:
            try:
                if paper_bot_state[0]!="Running" or mode.value!="Paper":raise ValueError("Start the Paper bot first")
                if not app_active[0]:raise ValueError("App is not active")
                mark=finite(paper_mark.value,"Manual mark",.000001);now=datetime.now().timestamp()
                if not bot_position.get("side"):
                    if not auto_reentry.value or not paper_last_exit:raise ValueError("No paper position; place an entry or enable re-entry")
                    if not paper_last_exit.get("known") or paper_risk_ledger().get("unknown_exits",0):raise ValueError("Unknown exit P&L blocks automatic paper re-entry")
                    if "stop" in paper_last_exit.get("reason","").lower() and not paper_reentry_after_sl.value:raise ValueError("Re-entry after stop-loss is OFF")
                    if now-paper_last_exit["time"]<int(cooldown.value)*60:raise ValueError("Paper re-entry cooldown active")
                    old=paper_last_exit["position"]
                    if bot_values()[4]!=old["contract"]:raise ValueError("Contract changed; start a new paper plan")
                    bot_premium.value=str(mark);prefs["bot_premium"]=mark
                    bot_paper_action(old["side"]);return
                settings={"trailing":bot_trailing.value,"trail_pct":paper_trail_pct.value,"partial":partial_profit.value,"partial_trigger":paper_partial_trigger.value,"partial_pct":paper_partial_pct.value,"average":buy_dip.value,"max_additions":int(paper_max_additions.value),"add_units":int(paper_add_units.value),"max_units":int(cash_max_quantity.value) if bot_position.get("segment")=="Cash" else int(max_total_lots.value),"dip_pct":dip_step.value}
                if bot_values()[4]!=bot_position["contract"]:raise ValueError("Contract changed; exit the existing paper position first")
                decision=evaluate_mark(bot_position,mark,settings)
                if decision["action"]=="EXIT":
                    bot_position.update(decision["position"]);paper_exit_price.value=str(mark);paper_exit_reason[0]=decision["reason"]
                    bot_paper_action("EXIT");return
                if decision["action"]=="ADD":
                    if emergency_stop.value:raise ValueError("Emergency stop blocks additions")
                    if now-float(bot_position.get("last_add_time",0))<int(cooldown.value)*60:raise ValueError("Addition cooldown active")
                    new=decision["position"];risk=check_trade_risk(new["entry"],new["quantity"],new["stop_price"])
                    ledger=paper_risk_ledger()
                    if float(ledger.get("realized_loss",0))>=float(max_daily_loss.value):raise ValueError("Daily realized paper loss limit reached")
                    extra=max(0,risk-abs(bot_position["entry"]-bot_position["stop_price"])*bot_position["quantity"])
                    if ledger["entries"]>=int(limit.value) or ledger["planned_risk_used"]+extra>float(max_daily_loss.value):raise ValueError("Daily paper limit blocks addition")
                    ledger["entries"]+=1;ledger["planned_risk_used"]+=extra;new["last_add_time"]=now
                    bot_position.update(new)
                elif decision["action"]=="PARTIAL":
                    qty=decision["quantity"];gross,net=paper_pnl(bot_position["side"],bot_position["entry"],mark,qty)
                    bot_position.update(decision["position"]);bot_position["quantity"]-=qty;bot_position["partial_done"]=True
                    prefs.setdefault("paper_journal",[]).append({"time":datetime.now(timezone.utc).isoformat(),"event":"PARTIAL","contract":bot_position["contract"],"quantity":qty,"entry":bot_position["entry"],"exit_price":mark,"paper_pnl":net,"reason":"Manual-mark paper partial; charges excluded"})
                else:bot_position.update(decision["position"])
                protection_sample.clear();prefs["bot_position"]=dict(bot_position)
                paper_state_status.value="Paper "+decision["action"]+" • "+decision.get("reason","")+" • manual mark "+str(mark)
                if decision["action"]=="ADD":prefs.setdefault("paper_journal",[]).append({"time":datetime.now(timezone.utc).isoformat(),"event":"ADD","contract":bot_position["contract"],"quantity":decision["quantity"],"entry":mark,"paper_pnl":None,"reason":"Manual-mark averaging; stop not widened"})
                prefs["paper_journal"]=prefs.get("paper_journal",[])[-200:]
                save();page.update()
            except (ValueError,TypeError,KeyError,OverflowError) as exc:paper_state_status.value="Paper tick blocked: "+str(exc);page.update()
    def paper_control_card():
        return section("PAPER BOT • MANUAL TICK ENGINE",ft.Column([paper_state_status,note("Start never enables real orders. Each Process mark press supplies one new manual price; phone lock pauses this engine. Stop blocks strategy actions but does not close a position."),ft.Row([ft.ElevatedButton("Start Paper",on_click=lambda e:paper_run("Start")),ft.OutlinedButton("Pause",on_click=lambda e:paper_run("Pause")),ft.OutlinedButton("Stop new actions",on_click=lambda e:paper_run("Stop"))],wrap=True),paper_mark,ft.TextButton("Process manual mark",on_click=paper_tick),cash_max_quantity,paper_max_additions,paper_add_units,paper_trail_pct,paper_partial_trigger,paper_partial_pct,paper_reentry_after_sl],horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    def paper_journal_card():
        rows=[]
        for item in reversed(prefs.get("paper_journal",[])[-10:]):
            rows.append(note(str(item["time"])+" • "+str(item["event"])+" • "+str(item.get("contract"))+" • Qty "+str(item.get("quantity"))+" • Paper P&L "+(str(item.get("paper_pnl")) if item.get("paper_pnl") is not None else "unknown")))
        return section("PAPER TRADE JOURNAL",ft.Column(rows or [note("No recorded entries/exits in this journal yet.")],spacing=6))
    def undo_setting(e=None):
        history=prefs.get("setting_changes",[])
        if not history:backup_status.value="No setting change to undo";page.update();return
        item=history[-1]
        control=next((c for c,k in field_bindings if k==item["key"]),None)
        if control is None or item["before"] is None:backup_status.value="This change cannot be restored";page.update();return
        old=control.value
        try:
            undoing[0]=True
            control.value=str(item["before"]) if isinstance(control,(ft.TextField,ft.Dropdown)) else item["before"]
            control.on_change(type("Undo",(),{"control":control})())
            if getattr(control,"error_text",None):raise ValueError("Previous value invalid")
            history.pop();save();backup_status.value="Previous setting restored"
        except (ValueError,TypeError):control.value=old;backup_status.value="Could not undo this change"
        finally:undoing[0]=False
        page.update()
    def backup_payload():
        allowed={k for _,k in field_bindings if k!="api_url"}
        allowed.update({"language","filter_modes","scanner_filters","scanner_added_filters","scanner_chart_indicators","scanner_chart_style","scanner_chart_visible","chart_provider","chart_views","last_page","page_scroll","option_strategy","paper_journal","paper_daily_limits","bot_position"})
        return {"app":"BOT KING","schema":1,"data":{k:v for k,v in prefs.items() if k in allowed}}
    def export_backup(e=None):
        backup_text.value=json.dumps(backup_payload(),ensure_ascii=False,indent=2)
        backup_status.value="Backup prepared. Copy and save this text outside the app. Credentials/API endpoint excluded."
        page.update()
    def copy_backup(e=None):
        export_backup()
        try:page.set_clipboard(backup_text.value);backup_status.value="Backup copied — paste it into a file or note before uninstalling"
        except Exception:backup_status.value="Select and copy the backup text manually"
        page.update()
    def import_backup(e=None):
        nonlocal market_status
        try:
            if not restore_confirm.value:raise ValueError("Tick confirmation before restoring settings")
            if bot_position.get("side"):raise ValueError("Exit the current PAPER position before restoring")
            if len(backup_text.value or "")>250000:raise ValueError("Backup is too large")
            payload=json.loads(backup_text.value)
            if payload.get("app")!="BOT KING" or payload.get("schema")!=1 or not isinstance(payload.get("data"),dict):raise ValueError("Invalid backup format")
            data=payload["data"];changes=[]
            for control,key in field_bindings:
                if key=="api_url" or key not in data:continue
                value=data[key]
                if isinstance(control,ft.Dropdown) and str(value) not in [str(x.key) for x in control.options]:raise ValueError("Unknown selection: "+key)
                if isinstance(control,(ft.Switch,ft.Checkbox)) and not isinstance(value,bool):raise ValueError("Invalid toggle: "+key)
                value=validate_field(control,key,value);changes.append((control,key,value))
            journal=data.get("paper_journal",[])
            if not isinstance(journal,list) or len(journal)>200:raise ValueError("Invalid journal")
            clean_journal=[]
            for row in journal:
                if (not isinstance(row,dict) or not isinstance(row.get("time"),str) or row.get("event") not in ("BUY","SELL","EXIT")
                        or not isinstance(row.get("contract"),(str,type(None))) or not isinstance(row.get("quantity"),(int,type(None)))):
                    raise ValueError("Invalid journal entry")
                datetime.fromisoformat(row["time"])
                clean_journal.append({k:row.get(k) for k in ("time","event","contract","quantity","entry","reason","paper_pnl")})
            # Never start automation or import an active position from a JSON file.
            for control,key,value in changes:
                prefs[key]=value;control.value=str(value) if isinstance(control,(ft.TextField,ft.Dropdown)) else value
            scan_live.value=False;prefs["scanner_live"]=False;protection_enabled.value=False;prefs["protection_enabled"]=False
            mode.value="Paper";prefs["mode"]="Paper"
            existing=prefs.get("paper_journal",[])
            for row in clean_journal:
                if row not in existing:existing.append(row)
            prefs["paper_journal"]=existing[-200:]
            for key,target in [("scanner_filters",filter_selected),("scanner_added_filters",added_filters)]:
                values=data.get(key)
                if isinstance(values,list) and all(isinstance(x,str) and x in ALL_FILTERS for x in values):target[:]=list(dict.fromkeys(values));prefs[key]=target[:]
            modes=data.get("filter_modes",{})
            if isinstance(modes,dict):
                for name,value in modes.items():
                    if name in ALL_FILTERS and value in ("Analysis","Chart","Both") and (name=="EMA 9/21" or value=="Analysis"):filter_modes[name]=value
                prefs["filter_modes"]=dict(filter_modes)
            if data.get("chart_provider") in ("TradingView Lightweight","BOT KING / Broker"):
                chart_provider[0]=data["chart_provider"];prefs["chart_provider"]=chart_provider[0]
            if data.get("scanner_chart_style") in ("Candlestick","Line"):
                scanner_chart_style[0]=data["scanner_chart_style"];prefs["scanner_chart_style"]=scanner_chart_style[0]
            if data.get("language") in ("English","हिंदी"):prefs["language"]=data["language"]
            refresh_option_expiry();update_expiry()
            protection_pending.clear();protection_sample.clear();protection_peak[0]=0
            market_status="Data source: "+source.value+" • waiting for refresh"
            connection_status.value=market_status
            provider_generation[0]+=1;scan_generation[0]+=1
            quotes.clear();candles.clear();fusion_cache.clear();mark_ranking_historical();scan_result.controls.clear()
            restore_confirm.value=False;save();backup_status.value="Settings restored; Auto Scan/protection OFF. Imported positions were not opened. Daily limits retained."
            select(current[0])
        except (ValueError,TypeError,KeyError,OverflowError) as exc:backup_status.value="Restore blocked: "+str(exc)
        page.update()
    backup_text=ft.TextField(label="Backup JSON • copy/export or paste to restore",multiline=True,min_lines=3,max_lines=8)
    backup_status=txt("Backup excludes API credentials. Store it privately outside the app.",12,MUTED)
    restore_confirm=ft.Checkbox(label="Replace normal settings from this backup; automatic actions stay OFF",value=False)
    def display_setting_time(value):
        try:
            stamp=datetime.fromisoformat(str(value))
            if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=timezone.utc)
            return stamp.astimezone(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %H:%M:%S IST")
        except (ValueError,TypeError,OverflowError):return "Time unavailable"
    def settings():
        if not angel_feed.connected and str(connection_status.value).startswith("Angel One connected"):
            connection_status.value="Broker disconnected or session expired; reconnect.";connection_status.color=GOLD
        content=[heading("Settings & Trading Bot"),status,note("All settings below • changes save automatically • credentials are not saved")]
        content.append(section('Broker & Data Source', ft.Column([broker, broker_info, source, credential_column, api_url, server_access, server_trust, ft.ElevatedButton('Dhan Login (only if server token missing)', on_click=open_dhan_authorization), ft.Row([ft.ElevatedButton('Connect / Check', on_click=explain_broker_connection, bgcolor=GOLD, color=BG), ft.OutlinedButton('Clear / Disconnect', on_click=clear_broker_credentials)], wrap=True), connection_status, note('Dhan read-only charts/scanner support 51 mapped NSE equities and NIFTY after Connect / Check with a server-side token. Yahoo and Angel One remain separate feeds. Dhan timestamps are unverified; no live orders.')])))
        content.extend([section('01  PAPER BOT', ft.Column([mode, note('Paper trading is simulated; no real orders are sent.')])), section('REAL TRADING • NOT CONNECTED',ft.Column([note('Real BUY / SELL requires verified Dhan or Angel One trading authorization, static-IP configuration, order status and explicit confirmation. Live order submission is DISABLED in this build.'),ft.ElevatedButton('REAL BUY • DISABLED',disabled=True),ft.ElevatedButton('REAL SELL • DISABLED',disabled=True)])), section('02  OPTION CONTRACT', ft.Column([bot_segment,bot_side,symbol_search(bot_symbol),bot_symbol, bot_custom,cash_quantity, ft.Row([bot_type, bot_strike], wrap=True), bot_expiry_mode, bot_expiry, expiry_warning, ft.Row([bot_lots, bot_lot_size], wrap=True), bot_premium,manual_contract_confirmed, note('Paper calculator uses manual premium and lot size. Connected broker quotes are shown on Options.')], spacing=12)), section('03  RISK & TARGET', ft.Column([ft.Row([sl, target], wrap=True),paper_capital,paper_notional_limit,paper_trade_risk,paper_risk_pct, limit, note('Paper trailing runs only when a new manual mark is processed. No live broker order is updated.'), ft.ElevatedButton('CALCULATE PLAN', on_click=calculate_bot, bgcolor=GOLD, color=BG), bot_preview], spacing=12)), section('04  PAPER STRATEGY • MANUAL TICKS', ft.Column([auto_entry, auto_reentry, buy_dip, partial_profit, bot_trailing, max_total_lots, dip_step, cooldown, max_daily_loss, squareoff, emergency_stop, note('Paper daily entry limit and cumulative planned-stop-risk budget are enforced. EXIT stays available. Realized paper losses use supplied exit prices and charges; blank exits remain unknown. Start can enter paper once; new manual ticks can re-enter, average, partially close and trail under configured limits. Square-off time remains a saved plan; no unattended or live orders.')], spacing=12)), section('05  PAPER TRADE CONTROLS', ft.Column([ft.Row([ft.ElevatedButton('BUY (Paper)', on_click=lambda e: bot_paper_action('BUY'), bgcolor=GREEN, color=BG), ft.ElevatedButton('SELL (Paper)', on_click=lambda e: bot_paper_action('SELL'), bgcolor=RED, color=BG), ft.OutlinedButton('EXIT', on_click=lambda e: bot_paper_action('EXIT'))], wrap=True), bot_trade_status,paper_exit_price,paper_exit_fees, note('Paper entries use manually entered prices. Start + Process manual mark can simulate SL/target exits; no live or background execution.')], spacing=12))])
        content.extend([
            section("POSITION PROTECTION • PAPER DEMONSTRATION",ft.Column([protection_mode,protection_enabled,protection_loss,protection_profit,protection_trail,protection_timeout,protection_no_reply,
                ft.ElevatedButton("Check PAPER position",on_click=check_paper_protection,bgcolor=GOLD,color=BG),ft.OutlinedButton("Confirm PAPER exit",on_click=lambda e:bot_paper_action("EXIT")),protection_status,
                note("No live broker orders or background server are connected. This demo evaluates manually entered premiums while the app is open. It cannot protect real money or operate after the phone closes the app.")],spacing=6)),
            paper_control_card(),paper_journal_card(),
            section("BACKUP / RESTORE",ft.Column([backup_text,ft.Row([ft.TextButton("Prepare backup",on_click=export_backup),ft.TextButton("Copy backup",on_click=copy_backup)],wrap=True),restore_confirm,ft.OutlinedButton("Restore normal settings",on_click=import_backup),backup_status],spacing=6)),
            section("SETTING CHANGE HISTORY",ft.Column([note(display_setting_time(item["time"])+" • "+item["key"]+": "+str(item["before"])+" → "+str(item["after"])) for item in reversed(prefs.get("setting_changes",[])[-8:])]+[ft.OutlinedButton("Undo last setting change",on_click=undo_setting)])),
            help_box("Risk and protection", "Paper limits are local simulations. Broker-side SL/target, filled-order confirmation and an always-on service are required before live automatic protection can be enabled."),
            section("06  SIGNAL FILTER",ft.Column([note("Minimum directional vote agreement — not success probability"),conf])),
            section("07  ALERTS • NOT CONNECTED",note("Notifications are unavailable until an alert delivery service is connected.")),
            section("08  BACKTEST • NOT CONNECTED",note("No backtest report exists in this build. Results must be validated before relying on strategies.")),
            section("09  DIAGNOSTICS",ft.Column([note("Recent error types only; API secrets and response bodies are excluded."),txt("\n".join(diagnostics[-10:]) or "No errors recorded this session",10,MUTED)])),

            note("Live broker orders are not connected. Paper strategy actions require Start and a new manual mark; square-off time is a saved preference only.")
        ])
        return content


    # Scanner-only upgrade. Existing five page functions remain unchanged.
    scanner_symbols=selection_symbols()
    saved_scanner_symbol=prefs.get("scanner_symbol","NIFTY")
    if saved_scanner_symbol not in scanner_symbols:
        scanner_symbols.append(saved_scanner_symbol)
    # The Dhan gateway currently verifies NIFTY and mapped NSE equities only.
    # Do not offer unsupported indexes as if their candles were available.
    if prefs.get("source","Dhan")=="Dhan":
        scanner_symbols=[v for v in scanner_symbols if v in DHAN_VERIFIED_SYMBOLS]
        if saved_scanner_symbol not in DHAN_VERIFIED_SYMBOLS:
            saved_scanner_symbol="NIFTY"
    scan_symbol=ft.Dropdown(label="Market / NSE stock",value=saved_scanner_symbol,options=[ft.dropdown.Option(v) for v in scanner_symbols])
    scan_budget=ft.Dropdown(label="Premium budget",value=prefs.get("scanner_budget","80-120"),options=[ft.dropdown.Option(v) for v in ["40-80","60-120","80-120","100-200","120-200","200-300","Custom","Any"]])
    scan_min=ft.TextField(label="Custom minimum (₹)",value=str(prefs.get("scanner_min","50")),keyboard_type=ft.KeyboardType.NUMBER)
    scan_max=ft.TextField(label="Custom maximum (₹)",value=str(prefs.get("scanner_max","500")),keyboard_type=ft.KeyboardType.NUMBER)
    scan_period=ft.Dropdown(label="Historical period",value=prefs.get("scanner_period","7d"),options=[ft.dropdown.Option(v) for v in ["7d","1mo","3mo"]])
    # Only expose intervals that the active Dhan gateway can actually fetch.
    scanner_intervals=(["1m","5m","15m","1h"] if prefs.get("source","Dhan")=="Dhan"
                       else ["1m","3m","5m","15m","30m","1h","1d"])
    saved_scanner_tf=prefs.get("scanner_timeframe","5m")
    if saved_scanner_tf not in scanner_intervals:
        saved_scanner_tf="5m"
    scan_tf=ft.Dropdown(label="Candle timeframe",value=saved_scanner_tf,options=[ft.dropdown.Option(v) for v in scanner_intervals])
    scan_expiry=ft.Dropdown(label="Illustrative days to expiry (NOT actual NSE expiry)",value=str(prefs.get("scanner_expiry","14")),options=[ft.dropdown.Option(v) for v in ["1","3","7","14","21","30"]])
    scan_auto=ft.Switch(label="Trend filter (simulation)",value=bool(prefs.get("scanner_trend",True)),active_color=GREEN)
    scan_live=ft.Switch(label="Auto Scan (while app is open)",value=bool(prefs.get("scanner_live",True)),active_color=GREEN)
    scan_refresh=ft.Dropdown(label="Auto refresh interval",value=str(prefs.get("scanner_refresh","30")),options=[ft.dropdown.Option(v) for v in ["30","60","120"]])
    scan_status=ft.Text("source candle history • automatic refresh follows saved preference",size=11,color=MUTED)
    if not scan_live.value:scan_status.value="Auto Scan OFF • saved preference"
    scan_last_candle=[None]
    scan_last_success=[None]
    scan_next_refresh=[None]
    scan_age_display=ft.Text("Last successful scan: — | Candle age: — | Next refresh: —",size=11,color=MUTED)
    filter_names=ALL_FILTERS[:]
    # One-time migration restores the original ten defaults without overriding later user edits.
    if not prefs.get("default_ten_migrated"):
        prefs["scanner_filters"]=DEFAULT_FILTERS[:]
        prefs["default_ten_migrated"]=True
    filter_selected=[x for x in prefs.get("scanner_filters",DEFAULT_FILTERS) if x in filter_names and x not in OPTION_FILTERS]
    added_filters=list(dict.fromkeys(x for x in prefs.get("scanner_added_filters",[])+filter_selected if x in filter_names and x not in DEFAULT_FILTERS))
    added_filter_list=ft.Column(spacing=8)
    def store_filters():
        scan_generation[0]+=1
        mark_ranking_historical()
        prefs["scanner_filters"]=filter_selected[:]
        prefs["scanner_added_filters"]=added_filters[:]
        save()
    def filter_availability(name):
        if name in ("OI Support","OI Resistance","OI Profile","Max Pain"):
            return "WAITING FOR DATA • verified option-chain feed not connected"
        if name in ("Volume","VWAP"):
            return "Analysis only • requires source volume; not a chart overlay"
        return "Analysis filter • not automatically drawn on chart"
    def remove_added_filter(name):
        if name in added_filters:added_filters.remove(name)
        if name in filter_selected:filter_selected.remove(name)
        filter_feedback.value="Removed "+name
        store_filters();select(3)
        if not scan_busy[0]:trigger_scan()
    filter_query=ft.TextField(label="Find indicator",dense=True)
    filter_choice=ft.Dropdown(label="Select filter",options=[ft.dropdown.Option(x) for x in filter_names],dense=True)
    filter_feedback=note("Active: "+", ".join(filter_selected))
    chart_filter_names=["EMA 9/21","RSI 14","MACD","Supertrend"]
    # Migrate the restricted widget to the app-fed chart once.
    if not prefs.get("lightweight_chart_migrated"):
        prefs["chart_provider"]="TradingView Lightweight"
        prefs["lightweight_chart_migrated"]=True
        save()
    chart_provider=[prefs.get("chart_provider","TradingView Lightweight")]
    if chart_provider[0]=="TradingView":chart_provider[0]="TradingView Lightweight"
    def tradingview_url(symbol):
        ticker={"NIFTY":"NSE:NIFTY","BANKNIFTY":"NSE:BANKNIFTY","SENSEX":"BSE:SENSEX"}.get(symbol,"NSE:"+symbol)
        return "https://www.tradingview.com/chart/?symbol="+urllib.parse.quote(ticker,safe="")+"&interval=5"
    tradingview_status=ft.Text("Lightweight chart: preparing...",size=12,color=MUTED)
    tv_view=[None]
    tv_booted=[False]
    tv_context=[None];tv_ready=[False];tv_js_view=[None];tv_history=[[]];tv_pending=[None];tv_limit=[300]
    def lightweight_payload(bars):
        import math
        rows={}
        for b in bars:
            try:
                t=int(b[0]);o,h,l,cl=map(float,b[1:5])
                if t>0 and all(math.isfinite(v) and v>0 for v in (o,h,l,cl)) and l<=min(o,cl)<=max(o,cl)<=h:
                    rows[t]={"time":t,"open":o,"high":h,"low":l,"close":cl}
            except (TypeError,ValueError,IndexError,OverflowError):
                continue
        return [rows[t] for t in sorted(rows)]
    def tradingview_widget_html(symbol, bars):
        payload=json.dumps(lightweight_payload(bars),allow_nan=False)
        options=json.dumps({"symbol":symbol,"timeframe":scan_tf.value,"line":scanner_chart_style[0]=="Line",
                            "ema":ema_on_chart(),"view":prefs.get("chart_views",{}).get(symbol+":"+str(scan_tf.value))}).replace("</","<\\/")
        return ('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0;height:100%;background:#080f18;color:#eaf1f6;font:12px sans-serif}
#header{height:62px;padding:6px 8px;box-sizing:border-box;overflow:hidden}#readout{font-size:11px;color:#a9bbc5}
#chart{height:calc(100% - 134px);width:100%;touch-action:none}#tools{height:36px;display:flex;gap:8px;padding:0 8px}button{background:#193443;color:#eaf1f6;border:1px solid #47616f;border-radius:5px;padding:5px 15px;font-size:15px}#credit{height:36px;padding:3px 8px;box-sizing:border-box;font-size:9px;color:#a9bbc5}a{color:#e9b949}</style>
</head><body><div id="header"><b id="status">Starting chart...</b><div id="readout"></div></div><div id="tools"><button id="zoomIn">＋</button><button id="zoomOut">−</button><button id="resetZoom">Reset</button><button id="moreHistory">More</button></div><div id="chart"></div>
<div id="credit">TradingView Lightweight Charts™<br>Copyright (с) 2024 TradingView, Inc. <a href="https://www.tradingview.com/">TradingView</a> · Apache 2.0</div>
<script>'''+LIGHTWEIGHT_CHARTS_JS.replace("</script","<\\/script")+'''</script><script>
(function(){
const status=document.getElementById('status'),readout=document.getElementById('readout');
function fail(e){status.textContent='Chart error: '+(e.message||e);console.log('BOT KING chart error: '+e)}
window.addEventListener('error',fail);
try{
const options='''+options+''';
const host=document.getElementById('chart');
const ist=t=>new Date(t*1000).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',hour12:false});
const chart=LightweightCharts.createChart(host,{width:host.clientWidth,height:host.clientHeight,layout:{background:{color:'#080f18'},textColor:'#a9bbc5'},grid:{vertLines:{color:'#16303b'},horzLines:{color:'#16303b'}},rightPriceScale:{borderColor:'#244350'},timeScale:{borderColor:'#244350',timeVisible:true,secondsVisible:false,tickMarkFormatter:t=>ist(t)},localization:{timeFormatter:ist},crosshair:{mode:LightweightCharts.CrosshairMode.Normal},handleScroll:true,handleScale:true});
const series=options.line?chart.addLineSeries({color:'#16c784',lineWidth:2}):chart.addCandlestickSeries({upColor:'#16c784',downColor:'#f05270',borderVisible:false,wickUpColor:'#16c784',wickDownColor:'#f05270'});
const ema9=options.ema?chart.addLineSeries({color:'#e9b949',lineWidth:1,priceLineVisible:false,lastValueVisible:false}):null;
const ema21=options.ema?chart.addLineSeries({color:'#72a7f2',lineWidth:1,priceLineVisible:false,lastValueVisible:false}):null;
function ema(data,n){let value=data[0].close;return data.map(b=>{value+=(b.close-value)*2/(n+1);return {time:b.time,value:value}})}
let first=true,latestText='',count=0,previous=[];
function resetView(){if(count)chart.timeScale().setVisibleLogicalRange({from:Math.max(0,count-70),to:count+3})}
function zoom(factor){const r=chart.timeScale().getVisibleLogicalRange();if(!r)return;const span=Math.max(8,Math.min(2000,(r.to-r.from)*factor));chart.timeScale().setVisibleLogicalRange({from:r.to-span,to:r.to})}
document.getElementById('zoomIn').onclick=()=>zoom(.7);
document.getElementById('zoomOut').onclick=()=>zoom(1.4);
document.getElementById('resetZoom').onclick=resetView;
document.getElementById('moreHistory').onclick=()=>console.log('BK_MORE');
window.botKingSetData=function(data){
 const value=b=>options.line?{time:b.time,value:b.close}:b;
 const samePrefix=previous.length && data.length>=previous.length && data.length<=previous.length+1 && previous.slice(0,-1).every((b,i)=>JSON.stringify(b)===JSON.stringify(data[i]));
 if(samePrefix){for(let i=previous.length-1;i<data.length;i++)series.update(value(data[i]))}else{series.setData(data.map(value))}
 previous=data;
 count=data.length;
 if(data.length){
  if(ema9){ema9.setData(ema(data,9));ema21.setData(ema(data,21))}
  latestText='Last candle: '+ist(data[data.length-1].time)+' IST · source candle history';
  status.textContent=options.symbol+' · '+options.timeframe+' · '+data.length+' candles';
  readout.textContent=latestText;
  if(first){
   if(options.view && Number.isFinite(options.view.from) && Number.isFinite(options.view.to) && options.view.to>options.view.from){chart.timeScale().setVisibleLogicalRange(options.view)}else{resetView()}
   first=false;
  }
 }else{status.textContent=options.symbol+' · No candles available';readout.textContent='Use Retry chart to fetch data.'}
};
chart.subscribeCrosshairMove(p=>{
 const b=p.seriesData.get(series);
 readout.textContent=b?(ist(p.time)+' IST · '+(options.line?'Price '+b.value.toFixed(2):'O '+b.open.toFixed(2)+' H '+b.high.toFixed(2)+' L '+b.low.toFixed(2)+' C '+b.close.toFixed(2))):latestText;
});
let viewTimer;
chart.timeScale().subscribeVisibleLogicalRangeChange(r=>{if(!r)return;clearTimeout(viewTimer);viewTimer=setTimeout(()=>console.log('BK_VIEW:'+JSON.stringify({symbol:options.symbol,timeframe:options.timeframe,from:r.from,to:r.to})),750)});
new ResizeObserver(()=>chart.applyOptions({width:host.clientWidth,height:host.clientHeight})).observe(host);
window.botKingSetData('''+payload+''');
console.log('BOT KING Lightweight Charts ready');
}catch(e){fail(e)}
})();
</script></body></html>''')
    def tv_set_status(message):
        tradingview_status.value=message
        try:
            if tradingview_status.page is not None:
                tradingview_status.update()
        except (AssertionError, RuntimeError):
            pass
    async def tv_load_widget():
        view=tv_view[0];context=tv_context[0]
        if view is None:return
        sym,interval,period,provider,style,ema,generation=context
        cached=candles.get("scanner_chart_"+provider+"_"+sym+"_"+interval+"_"+period) or market_store.get("market",provider,sym,interval,period) or {}
        # A scanner/watchlist candle request may have completed under a
        # different period (7d vs 5d). Reuse same-symbol, same-timeframe Dhan
        # history rather than showing a blank chart or making another request.
        # Never reuse candles from a different provider/generation/timeframe.
        if not cached.get("bars"):
            with market_registry_lock:
                matching=[(stamp, data) for key,(stamp,data) in market_recent.items()
                          if key[0]==generation and key[3]==provider
                          and key[4]==sym and key[5]==interval
                          and isinstance(data,dict) and data.get("bars")]
            if matching:
                cached=max(matching,key=lambda item:item[0])[1]
        # The independent watchlist/history scan may already have valid candles
        # for this symbol. Reuse them during Dhan cooldown rather than showing
        # a blank chart; never treat a quote-only snapshot as candle history.
        if not cached.get("bars"):
            shared=quotes.get(sym) or {}
            if shared.get("source")==provider and shared.get("bars") and interval=="5m":
                cached=shared
        try:
            if tv_js_view[0] is not view:
                await asyncio.to_thread(view.invoke_method,"set_javascript_mode",arguments={"value":"true"},wait_for_result=True,wait_timeout=10)
                tv_js_view[0]=view
            if view is not tv_view[0]:return
            loaded=False
            if cached.get("bars"):
                tv_history[0]=cached["bars"]
                view.load_html(tradingview_widget_html(sym,tv_history[0][-tv_limit[0]:]),base_url="https://www.tradingview.com/")
                loaded=True
                tv_set_status("Saved chart visible • checking newer data...")
            # Do not spend a doomed history request while the Dhan upstream
            # cooldown is active. A saved candle chart remains usable.
            if provider=="Dhan" and dhan_feed.cooldown_remaining("/dhan/intraday")>0:
                tv_set_status(("Saved historical chart • " if loaded else "Chart unavailable • no saved candles • ")+"Dhan API cooldown active; retry later")
                return
            hist=await asyncio.to_thread(get_market_data,sym,interval,period)
            if view is not tv_view[0] or context!=tv_context[0] or generation!=provider_generation[0]:return
            candles["scanner_chart_"+provider+"_"+sym+"_"+interval+"_"+period]=hist
            # Chart history must never overwrite the independent Dhan LTP snapshot.
            tv_history[0]=hist.get("bars") or []
            tv_pending[0]=tv_history[0][-tv_limit[0]:]
            if not loaded:view.load_html(tradingview_widget_html(sym,tv_pending[0]),base_url="https://www.tradingview.com/")
            elif tv_ready[0]:push_chart_data()
        except Exception as exc:
            log_error("chart",exc)
            tv_set_status(("Chart refresh failed • saved chart retained" if loaded else "Chart unavailable • no saved candles")+" • "+safe_error(exc)+" • Retry available")
    def push_chart_data():
        if tv_view[0] is not None and tv_ready[0] and tv_pending[0] is not None:
            tv_view[0].run_javascript("window.botKingSetData("+json.dumps(lightweight_payload(tv_pending[0]),allow_nan=False)+");")
            tv_pending[0]=None
            tv_set_status("Chart ready • "+str(min(tv_limit[0],len(tv_history[0])))+" candles displayed • More loads older history")
    def tv_started(e):
        if e.control is tv_view[0] and not tv_ready[0]:tv_set_status("Chart initializing...")
    def tv_ended(e):
        if e.control is not tv_view[0]:return
        if not tv_booted[0]:
            tv_booted[0]=True
            page.run_task(tv_load_widget)
        else:
            tv_set_status("Lightweight chart loaded • source candle history • touch to inspect; see DATA SOURCE for actual provider")
    def chart_console(e):
        try:
            import math
            message=e.message
            if getattr(e,"control",tv_view[0]) is not tv_view[0]:return
            if message=="BOT KING Lightweight Charts ready":
                tv_ready[0]=True;push_chart_data()
                tv_set_status("Chart ready • touch to inspect • More loads older history");return
            if message=="BK_MORE":
                tv_limit[0]=min(len(tv_history[0]),tv_limit[0]+300)
                tv_pending[0]=tv_history[0][-tv_limit[0]:];push_chart_data();return
            if not message.startswith("BK_VIEW:"):return
            v=json.loads(message[8:]);lo=float(v["from"]);hi=float(v["to"])
            if not (math.isfinite(lo) and math.isfinite(hi) and 0<hi-lo<=100000):return
            if v["symbol"]!=scan_symbol.value or v["timeframe"]!=scan_tf.value:return
            prefs.setdefault("chart_views",{})[v["symbol"]+":"+v["timeframe"]]={"from":lo,"to":hi}
            save()
        except (ValueError,TypeError,KeyError,AttributeError):pass
    def tv_error(e):
        tv_set_status("TradingView resource error: "+str(e.data)[:220])
    def tv_retry(e):
        if tv_view[0] is not None:
            page.run_task(tv_load_widget)
    def chart_provider_change(e):
        tv_view[0]=None;tv_context[0]=None;tv_ready[0]=False;tv_booted[0]=False;tv_js_view[0]=None
        chart_provider[0]=e.control.value
        prefs["chart_provider"]=chart_provider[0]
        save()
        select(3)
    filter_checklist=ft.Column(spacing=0)
    def reset_default_filters(e):
        scan_generation[0]+=1
        mark_ranking_historical()
        filter_selected[:]=DEFAULT_FILTERS[:]
        added_filters.clear();prefs["scanner_added_filters"]=[]
        scanner_chart_indicators[:]=chart_filter_names[:]
        prefs["scanner_filters"]=filter_selected[:]
        prefs["scanner_chart_indicators"]=scanner_chart_indicators[:]
        save();select(3)
        if not scan_busy[0]:trigger_scan()
    def filter_checkbox_changed(e):
        name=e.control.data
        if name in OPTION_FILTERS:
            filter_feedback.value="Unavailable: verified option-chain OI/PCR data not connected"
            select(3)
            return
        if e.control.value and name not in filter_selected:filter_selected.append(name)
        elif not e.control.value and name in filter_selected:filter_selected.remove(name)
        store_filters();select(3)
        if not scan_busy[0]:trigger_scan()
    def filter_edit(add):
        q=(filter_query.value.strip() if filter_query.value and filter_query.value.strip() else filter_choice.value or "").lower()
        hits=([x for x in filter_names if q==x.lower()] or [x for x in filter_names if q and q in x.lower()])
        if len(hits)!=1:
            filter_feedback.value="Select one supported filter"
        else:
            name=hits[0]
            if add:
                if name in OPTION_FILTERS:
                    filter_feedback.value="Unavailable: verified option-chain OI/PCR feed required"
                    return
                if name not in filter_selected:filter_selected.append(name)
                if name not in DEFAULT_FILTERS and name not in added_filters:added_filters.append(name)
                filter_feedback.value="Selected "+name+" • "+filter_availability(name)
            else:
                if name in filter_selected:filter_selected.remove(name)
                if name in added_filters:added_filters.remove(name)
                filter_feedback.value="Removed "+name
        filter_query.value=""
        store_filters();select(3)
        if not scan_busy[0]:trigger_scan()
    scan_auto_generation=[0]
    def refresh_scan_age():
        now=datetime.now().timestamp()
        last=(str(max(0,int(now-scan_last_success[0])))+" sec ago") if scan_last_success[0] is not None else "—"
        candle=(str(max(0,int(now-scan_last_candle[0])))+" sec") if scan_last_candle[0] is not None else "—"
        if not scan_live.value:
            next_text="OFF";scan_next_refresh[0]=None
        elif not app_active[0]:
            next_text="PAUSED — app in background"
        elif prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):
            next_text="PAUSED — select a market feed";scan_next_refresh[0]=None
        elif not regular_hours():
            next_text="PAUSED — outside regular session hours";scan_next_refresh[0]=None
        elif scan_busy[0]:next_text="checking history now"
        elif scan_next_refresh[0] is None:next_text="waiting"
        else:next_text=str(max(0,int(scan_next_refresh[0]-now)))+" sec"
        scan_age_display.value="Last scan: "+last+" | Candle age: "+candle+" | Next auto refresh: "+next_text
    async def scan_age_clock():
        while True:
            refresh_scan_age()
            if current[0]==3:
                try:scan_age_display.update()
                except (AssertionError,RuntimeError):pass
            await asyncio.sleep(1)
    def auto_scan_changed(e):
        scan_auto_generation[0]+=1
        scan_status.value=("Auto Scan ON • checking for new source candles" if scan_live.value
                           else "Auto Scan OFF")
        refresh_scan_age()
        page.update()
        if scan_live.value:
            page.run_task(auto_scan_loop,scan_auto_generation[0])
    # Fast local signal pass: never calls Dhan or treats saved/stale candles as live.
    # A signal can change only when a newer verified-source candle arrives.
    scan_fast_seen=[None]
    def refresh_cached_scanner_signal():
        if not app_active[0] or scan_busy[0] or not regular_hours():
            return
        sym=scan_symbol.value or "NIFTY"
        tf=scan_tf.value or "5m"
        snapshot=candles.get("scanner_chart_"+sym)
        if (not isinstance(snapshot,dict) or snapshot.get("cached")
                or snapshot.get("source") not in ("dhan","Dhan")
                or snapshot.get("_scanner_timeframe")!=tf
                or snapshot.get("_scanner_generation")!=scan_generation[0]):
            return
        bars=snapshot.get("bars")
        if not isinstance(bars,list) or len(bars)<30:
            return
        last=bars[-1][0]
        identity=(scan_generation[0],sym,tf,last)
        if identity==scan_fast_seen[0]:
            return
        result=analyze_current(bars,filter_selected,tf)
        if result.get("timestamp")!=last:
            return
        scan_fast_seen[0]=identity
        scan_shared.update(direction=result["bias"],basis=result["reason"],tf=tf,symbol=sym,timestamp=last)
        if current[0]==0:
            request_view_refresh(0)
    async def scanner_fast_signal_loop():
        while True:
            try:
                if scan_live.value and prefs.get("source")=="Dhan" and dhan_feed.connected:
                    refresh_cached_scanner_signal()
            except Exception as exc:
                log_error("scanner_fast_signal",exc)
            await asyncio.sleep(20)
    async def auto_scan_loop(generation):
        # No background service: refresh runs only while this app/page is alive.
        initial=True
        while scan_live.value and generation==scan_auto_generation[0]:
            if prefs.get("source")=="Dhan" and not dhan_feed.connected:
                scan_next_refresh[0]=None
                scan_status.value="Dhan login required • automatic scan paused"
                await asyncio.sleep(5);continue
            if not app_active[0]:
                scan_next_refresh[0]=None
                await asyncio.sleep(5);continue
            if not initial and not regular_hours():
                scan_next_refresh[0]=None
                scan_status.value=session_caption()
                refresh_scan_age()
                if current[0]==3:page.update()
                await asyncio.sleep(30)
                continue
            initial=False
            try:
                delay=int(scan_refresh.value or "60")
            except (ValueError,TypeError):
                delay=60
            if not scan_busy[0] and (scan_next_refresh[0] is None or datetime.now().timestamp()>=scan_next_refresh[0]):
                scan_busy[0]=True
                try:await scan_market()
                except Exception as exc:
                    log_error("auto_scan",exc);scan_busy[0]=False
                scan_next_refresh[0]=datetime.now().timestamp()+max(30,delay)
            refresh_scan_age()
            # Short ticks make source changes, refresh interval changes and resume responsive.
            await asyncio.sleep(1)
    scan_live.on_change=auto_scan_changed
    def trigger_scan(e=None):
        prefs["scanner_symbol"]=scan_symbol.value or "NIFTY"
        prefs["scanner_timeframe"]=scan_tf.value or "5m"
        save()
        if e is not None and e.control in (scan_symbol,scan_tf,scan_period):
            scan_generation[0]+=1
            # Explicit selection changes reload the chart; background scans do not.
            scan_result.controls.clear()
            candles.pop("scanner_chart_"+(scan_symbol.value or "NIFTY"),None)
            if current[0]==3:select(3)
        if e is not None and e.control is scan_budget:
            scan_min.visible=scan_budget.value=="Custom";scan_max.visible=scan_budget.value=="Custom"
            page.update()
        if scan_tf.value in ("1m","3m"):
            scan_period.value="7d";prefs["scanner_period"]="7d";save()
        if not scan_busy[0]:
            scan_busy[0]=True
            page.run_task(scan_market)
    for c in [scan_symbol,scan_budget,scan_min,scan_max,scan_period,scan_tf,scan_expiry,scan_auto]:
        c.on_change=trigger_scan
    scan_result=ft.Column(spacing=12)
    scan_busy=[False]
    def scan_num(x):
        return f"{x:,.2f}" if isinstance(x,(float,int)) else "—"
    scanner_chart_visible=[bool(prefs.get("scanner_chart_visible",True))]
    scanner_chart_indicators=[x for x in prefs.get("scanner_chart_indicators",chart_filter_names) if x in chart_filter_names]
    scanner_chart_style=[prefs.get("scanner_chart_style","Candlestick")]
    def scanner_chart_toggle(e):
        tv_view[0]=None;tv_context[0]=None;tv_ready[0]=False;tv_booted[0]=False;tv_js_view[0]=None
        scanner_chart_visible[0]=not scanner_chart_visible[0]
        prefs["scanner_chart_visible"]=scanner_chart_visible[0];save()
        select(3)
    def filter_mode_changed(e):
        name=e.control.data;mode=e.control.value
        if name!="EMA 9/21" and mode!="Analysis":return
        filter_modes[name]=mode
        prefs["filter_modes"]=dict(filter_modes);save()
        scan_generation[0]+=1
        select(3)
        if not scan_busy[0]:trigger_scan()
    def filter_mode_control(name):
        choices=["Analysis","Chart","Both"] if name=="EMA 9/21" else ["Analysis"]
        mode=filter_modes.get(name,"Both" if name=="EMA 9/21" else "Analysis")
        if mode not in choices:mode="Analysis"
        return ft.Dropdown(label="Use for" if name=="EMA 9/21" else "Use for • chart overlay not implemented",value=mode,data=name,options=[ft.dropdown.Option(x) for x in choices],on_change=filter_mode_changed)
    def scanner_chart_filter(e):
        # Chart visibility is independent of the ten active background analysis filters.
        name=e.control.data
        if e.control.value and name not in scanner_chart_indicators:scanner_chart_indicators.append(name)
        if not e.control.value and name in scanner_chart_indicators:scanner_chart_indicators.remove(name)
        prefs["scanner_chart_indicators"]=scanner_chart_indicators[:]
        if name=="EMA 9/21":filter_modes[name]="Both" if e.control.value else "Analysis";prefs["filter_modes"]=dict(filter_modes)
        save();select(3)
    def scanner_chart_style_change(e):
        scanner_chart_style[0]=e.control.value
        prefs["scanner_chart_style"]=scanner_chart_style[0]
        save()
        select(3)
    def choose_timeframe(value):
        scan_tf.value=value
        prefs["scanner_timeframe"]=value;save()
        trigger_scan(type("TimeframeChange",(),{"control":scan_tf})())
    def scanner_compact_chart():
        sym=scan_symbol.value or "NIFTY"
        saved_chart=candles.get("scanner_chart_"+sym) or {}
        if (saved_chart.get("_scanner_timeframe") != (scan_tf.value or "5m")
                or saved_chart.get("_scanner_generation") != scan_generation[0]):
            saved_chart={}
        hist=saved_chart or market_store.get("market",prefs.get("source","Dhan"),sym,scan_tf.value or "5m",scan_period.value or "7d") or {}
        # Validate cached and persisted candles before either mini-chart renderer.
        # Never allow duplicate, reversed, or malformed timestamps into a chart.
        bars=clean_bars(hist.get("bars") or [])[-35:]
        parts=[ft.Row([txt(sym+" • "+(scan_tf.value or "5m"),15,GOLD,True),ft.TextButton("Hide" if scanner_chart_visible[0] else "Show",on_click=scanner_chart_toggle)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)]
        if scanner_chart_visible[0]:
            parts.append(ft.Row([ft.TextButton(v,on_click=lambda e,t=v:choose_timeframe(t),style=ft.ButtonStyle(color=GOLD if scan_tf.value==v else MUTED)) for v in ["1m","3m","5m","15m","30m","1h","1d"]],wrap=True,spacing=2,run_spacing=2))
            parts.append(note(session_caption()))
            parts.append(ft.Dropdown(label="Chart display",value=scanner_chart_style[0],options=[ft.dropdown.Option("Candlestick"),ft.dropdown.Option("Line")],on_change=scanner_chart_style_change,dense=True))
            parts.append(ft.Dropdown(label="Chart provider",value=chart_provider[0],options=[ft.dropdown.Option("TradingView Lightweight"),ft.dropdown.Option("BOT KING / Broker")],on_change=chart_provider_change,dense=True))
            if chart_provider[0]=="TradingView Lightweight":
                parts.append(note("TradingView Lightweight Charts • source OHLC • ＋ / − / Reset or pinch • EMA 9/21 overlay only; other filters are analysis, not plotted overlays."))
                parts.append(note("Chart/Analysis/Both is selected per filter below. Only EMA currently has a chart overlay."))
                parts.append(tradingview_status)
                context=(sym,scan_tf.value or "5m",scan_period.value or "7d",prefs.get("source","Dhan"),scanner_chart_style[0],ema_on_chart(),provider_generation[0])
                if tv_view[0] is None or tv_context[0]!=context:
                    tv_context[0]=context;tv_booted[0]=False;tv_ready[0]=False;tv_pending[0]=None;tv_limit[0]=300
                    tv_view[0]=ft.WebView(url="about:blank",enable_javascript=True,expand=True,on_page_started=tv_started,on_page_ended=tv_ended,on_web_resource_error=tv_error,on_console_message=chart_console)
                parts.append(ft.Container(content=tv_view[0],height=460,bgcolor=PANEL2,border_radius=8))
                parts.append(ft.Row([ft.TextButton("Retry chart",on_click=tv_retry),ft.TextButton("Open in browser",on_click=lambda e: page.launch_url(tradingview_url(sym)))],wrap=True))
                parts.append(note("If chart loading fails, select BOT KING / Broker from Chart provider."))
                return section("LIGHTWEIGHT CHART • "+sym,ft.Column(parts,spacing=4))
            parts.append(note("Underlying OHLC • delayed historical candles, NOT option premium"))
            if len(bars)>=2:
                closes=[float(b[4]) for b in bars]
                lows=[float(b[3]) for b in bars]
                highs=[float(b[2]) for b in bars]
                low=min(lows);high=max(highs);spread=max(high-low,.01)
                if scanner_chart_style[0]=="Line":
                    points=[ft.LineChartDataPoint(i,v) for i,v in enumerate(closes)]
                    series=[ft.LineChartData(data_points=points,stroke_width=2,color=GREEN,curved=False)]
                    if "EMA 9/21" in scanner_chart_indicators:
                        for length,color in [(9,GOLD),(21,"#72A7F2")]:
                            alpha=2/(length+1);z=closes[0];vals=[]
                            for i,v in enumerate(closes):
                                z=alpha*v+(1-alpha)*z
                                vals.append(ft.LineChartDataPoint(i,z))
                            series.append(ft.LineChartData(data_points=vals,stroke_width=1.5,color=color,curved=False))
                    visual=ft.LineChart(data_series=series,min_x=0,max_x=len(closes)-1,min_y=low-spread*.12,max_y=high+spread*.12,left_axis=ft.ChartAxis(labels_size=48),bottom_axis=ft.ChartAxis(labels_size=0),right_axis=ft.ChartAxis(labels_size=0),top_axis=ft.ChartAxis(labels_size=0),expand=True)
                else:
                    width=300;height=180;controls=[]
                    for i,(_,o,h,l,c,v) in enumerate(bars):
                        x=i*width/len(bars)+2
                        yy=lambda p:8+(high-float(p))/spread*(height-16)
                        color=GREEN if c>=o else RED
                        controls.append(ft.Container(left=x+2,top=yy(h),width=2,height=max(1,yy(l)-yy(h)),bgcolor=color))
                        controls.append(ft.Container(left=x,top=min(yy(o),yy(c)),width=max(3,width/len(bars)-2),height=max(2,abs(yy(c)-yy(o))),bgcolor=color))
                    if "EMA 9/21" in scanner_chart_indicators:
                        for length,color in [(9,GOLD),(21,"#72A7F2")]:
                            z=closes[0]
                            for i,v in enumerate(closes):
                                z+=2*(v-z)/(length+1)
                                controls.append(ft.Container(left=i*width/len(bars)+3,top=yy(z),width=3,height=3,bgcolor=color))
                    visual=ft.Stack(controls,width=width,height=height)
                parts.append(ft.Container(content=visual,height=190,alignment=ft.alignment.center))
                parts.append(note(f"Index range {low:,.2f} – {high:,.2f}" if (scan_symbol.value or "NIFTY") in ("NIFTY","BANKNIFTY","SENSEX") else f"Price range ₹{low:,.2f} – ₹{high:,.2f}"))
                if "RSI 14" in scanner_chart_indicators and len(closes)>=15:
                    dif=[closes[i]-closes[i-1] for i in range(-14,0)]
                    gain=sum(max(0,x) for x in dif);loss=sum(max(0,-x) for x in dif)
                    value=100 if loss==0 else 100-100/(1+gain/loss)
                    parts.append(note(f"RSI 14: {value:.1f}"))
                if "MACD" in scanner_chart_indicators:
                    def ema_series(n):
                        z=closes[0];out=[]
                        for v in closes:z+=2*(v-z)/(n+1);out.append(z)
                        return out
                    m=[x-y for x,y in zip(ema_series(12),ema_series(26))]
                    z=m[0]
                    for v in m:z+=2*(v-z)/10
                    parts.append(note(f"MACD: {m[-1]:.2f} • Signal: {z:.2f}"))
                if "Supertrend" in scanner_chart_indicators:
                    parts.append(note("Supertrend signal: see Analysis Basis; no fabricated overlay"))
            else:parts.append(note("Chart will appear after a successful scanner fetch."))
            parts.append(ft.Column([ft.Checkbox(label=x,value=x in scanner_chart_indicators,data=x,on_change=scanner_chart_filter) for x in chart_filter_names],spacing=0))
            parts.append(note("Chart switches affect display only. The 10 analysis filters below work independently. EMA is plotted; RSI/MACD show values; Supertrend shows analysis status."))
            parts.append(note("OI / PCR / Max Pain context is shown below when a matching Dhan Options snapshot exists; not a live scanner vote."))
        return section("COMPACT CHART • "+sym,ft.Column(parts,spacing=4))
    def scanner_option_context():
        """Display cached Dhan option metrics without treating them as scanner votes."""
        symbol=scan_symbol.value or "NIFTY"
        data=dhan_option_metrics
        if symbol!="NIFTY":
            message="OI / PCR / Max Pain: unavailable for "+symbol+" • Dhan option mapping verified only for NIFTY"
        elif (prefs.get("source")!="Dhan" or not dhan_feed.connected
              or data.get("symbol")!="NIFTY" or data.get("expiry")!=expiry.value):
            message="OI / PCR / Max Pain: no matching Dhan expiry snapshot • open Options and refresh selected data"
        else:
            message=("Dhan NIFTY • expiry "+str(data["expiry"])
                     +" • PCR "+f'{data["pcr"]:.3f}'
                     +" • Max Pain "+f'{data["max_pain"]:,.0f}'
                     +" • OI strike levels unavailable")
        return section("OI / PCR / MAX PAIN • INFORMATION ONLY",
                       ft.Column([note(message),
                                  note("Freshness UNVERIFIED • no OI/PCR/Max Pain scanner vote or live trade signal")],spacing=4))
    def scanner():
        fusion_selected.controls=[fusion_card(scan_symbol.value or "NIFTY",scan_tf.value or "5m")]
        filter_checklist.controls=[ft.Container(content=ft.Column([ft.Checkbox(label=x,value=x in filter_selected,data=x,on_change=filter_checkbox_changed),filter_mode_control(x)],spacing=5),padding=ft.padding.symmetric(horizontal=6,vertical=9),border=ft.border.only(bottom=ft.BorderSide(1,BORDER))) for x in DEFAULT_FILTERS]
        added_filter_list.controls=[ft.Container(content=ft.Column([
            ft.Checkbox(label=name,value=name in filter_selected,data=name,on_change=filter_checkbox_changed),
            note(filter_availability(name)),
            ft.OutlinedButton("Remove ×",on_click=lambda e,n=name:remove_added_filter(n)),filter_mode_control(name)
        ],spacing=3),padding=8,bgcolor=PANEL2,border_radius=8) for name in added_filters]
        if not added_filters:added_filter_list.controls=[note("No extra filters added. Add below; each extra filter will appear here.")]
        scan_min.visible=scan_budget.value=="Custom"
        scan_max.visible=scan_budget.value=="Custom"
        return [heading("RULE-BASED SCANNER • Chart & Analysis"),
            note("Selected-source underlying candles • simulated premiums, not live contracts"),
            card(symbol_search(scan_symbol),scan_symbol,scan_tf,scan_budget,scan_period,scan_min,scan_max,scan_expiry,scan_refresh,
                 scan_live,ft.ElevatedButton("Refresh history now",on_click=run_scan),scan_status,scan_age_display),
            scanner_compact_chart(),fusion_selected,scanner_option_context(),
            section("10 DEFAULT ANALYSIS FILTERS • ON/OFF",ft.Column([note("These control background scanner votes and Top 5 ranking, not chart visibility."),filter_checklist,ft.OutlinedButton("Restore default 10",on_click=reset_default_filters),note("Additional indicators: choose below; OI/PCR require verified exchange data.")],spacing=4)),section("ADDED FILTERS • "+str(len(added_filters))+" saved • "+str(sum(n in filter_selected for n in added_filters))+" ON",added_filter_list),section("ADD EXTRA FILTERS • Saved",ft.Column([filter_query,filter_choice,ft.Row([ft.ElevatedButton("Add",on_click=lambda e:filter_edit(True)),ft.OutlinedButton("Remove",on_click=lambda e:filter_edit(False))]),filter_feedback,note("Unavailable data cannot vote. Adding a filter does not imply a plotted overlay.")],spacing=5)),
            scan_result,help_box("Scanner", "Analysis/Chart/Both routes a filter only to supported functions. Headline sentiment is experimental. WAIT can mean stale or missing data, not a sideways prediction.")]
    def run_scan(e):
        if prefs.get("source")=="Dhan" and not dhan_feed.connected:
            scan_status.value="Dhan login required • scan paused"
            page.update()
            return
        if scan_busy[0]:return
        scan_busy[0]=True
        if not scan_live.value:
            scan_result.controls=[card(txt("Checking selected market data…",16,GOLD,True))]
        page.update()
        page.run_task(scan_market)
    async def restart_latest_scan():
        await asyncio.sleep(.05)
        if not scan_busy[0]:
            scan_busy[0]=True
            await scan_market()
    async def scan_market():
        nonlocal market_status
        if prefs.get("source")=="Dhan" and not dhan_feed.connected:
            scan_status.value="Dhan login required • scan paused"
            scan_busy[0]=False
            return
        generation=scan_generation[0]
        import math
        from datetime import timezone
        try:
            sym=scan_symbol.value or "NIFTY"
            period=scan_period.value or "1mo"
            interval=scan_tf.value or "1d"
            # Intraday history depends on the connected broker feed.
            if interval in ("1m","3m") and period!="7d":
                raise ValueError("Broker 1m history may be limited. Select 7d.")
            if interval=="5m" and period=="3mo":
                raise ValueError("Broker 5m candles may not cover 3 months. Choose 7d or 1mo.")
            if interval in ("5m","15m","30m") and period=="3mo":
                raise ValueError("Broker intraday history may be limited. Choose 7d or 1mo.")
            hist=await asyncio.wait_for(asyncio.to_thread(get_market_data,sym,interval,period),timeout=45)
            if generation!=scan_generation[0] or sym!=scan_symbol.value or interval!=scan_tf.value:return
            bars=hist.get("bars") or []
            candles["scanner_chart_"+sym]=dict(hist,_scanner_timeframe=interval,
                                              _scanner_generation=generation)
            # Scanner historical candles must never replace the separately polled
            # Dhan equity LTP with a missing/unverified history-only price.
            if prefs.get("source")!="Dhan":
                quotes[sym]=hist
            market_status="Data source: "+hist.get("source","Unavailable")+" • "+quote_caption(sym)
            # Push fresh bars into the existing chart without losing zoom or reloading.
            if (current[0]==3 and chart_provider[0]=="TradingView Lightweight"
                    and tv_view[0] is not None and sym==scan_symbol.value and interval==scan_tf.value):
                try:
                    data=json.dumps(lightweight_payload(bars[-tv_limit[0]:]),allow_nan=False)
                    tv_history[0]=bars
                    tv_view[0].run_javascript("if(window.botKingSetData){window.botKingSetData("+data+");}")
                except Exception as exc:
                    tv_set_status("Chart update failed: "+str(exc)[:120])
            closes=[float(b[4]) for b in bars if b[4] is not None and b[4]>0]
            if len(closes)<8:raise ValueError("Not enough valid broker candles. Choose a longer period or daily timeframe.")
            latest_timestamp=bars[-1][0]
            scan_last_candle[0]=latest_timestamp
            updated=datetime.fromtimestamp(latest_timestamp,timezone.utc)
            age_hours=(datetime.now(timezone.utc)-updated).total_seconds()/3600
            price=closes[-1]
            first=closes[0]
            change=(price/first-1)*100
            # Estimate annual volatility using selected candle duration; for illustrative pricing only.
            annual_bars=timeframe_spec(interval)["annual_bars"]
            returns=[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes))]
            avg=sum(returns)/len(returns)
            variance=sum((v-avg)**2 for v in returns)/max(1,len(returns)-1)
            volatility=max(.08,min(1.5,math.sqrt(variance*annual_bars)))
            ma_fast=sum(closes[-min(5,len(closes)):])/min(5,len(closes))
            ma_slow=sum(closes[-min(20,len(closes)):])/min(20,len(closes))
            def ema(vals,n):
                z=vals[0];out=[z]
                for v in vals[1:]:z+=2*(v-z)/(n+1);out.append(z)
                return out
            votes=[]
            if "SMA 5/20" in filter_selected:votes.append(("SMA 5/20",1 if price>ma_fast>=ma_slow else -1 if price<ma_fast<=ma_slow else 0,"5="+scan_num(ma_fast)+" 20="+scan_num(ma_slow)))
            if "EMA 9/21" in filter_selected:
                x=ema(closes,9)[-1];y=ema(closes,21)[-1]
                votes.append(("EMA 9/21",1 if price>x>y else -1 if price<x<y else 0,"9="+scan_num(x)+" 21="+scan_num(y)))
            if "RSI 14" in filter_selected:
                dif=[closes[i]-closes[i-1] for i in range(1,len(closes))]
                g=sum(max(0,v) for v in dif[-14:]);l=sum(max(0,-v) for v in dif[-14:])
                val=100 if l==0 else 100-100/(1+g/l)
                votes.append(("RSI 14",1 if 52<=val<=70 else -1 if 30<=val<=48 else 0,f"RSI={val:.1f}"))
            if "MACD" in filter_selected:
                line=[x-y for x,y in zip(ema(closes,12),ema(closes,26))]
                sig=ema(line,9)[-1]
                votes.append(("MACD",1 if line[-1]>sig else -1 if line[-1]<sig else 0,"MACD="+scan_num(line[-1])+" signal="+scan_num(sig)))
            up=sum(v==1 for _,v,_ in votes);down=sum(v==-1 for _,v,_ in votes)
            direction="BULLISH" if up>=2 and up>=2*down else "BEARISH" if down>=2 and down>=2*up else "SIDEWAYS / WAIT"
            advanced=analyze_current(bars,filter_selected,interval)
            if hist.get("cached"):
                advanced.update(bias="WAIT",score=0,reason=advanced["reason"]+" • Saved data only: refresh failed; no new live signal")
            direction=advanced["bias"]
            basis=advanced["reason"]
            # Publish candle results before RSS requests so missing/slow news cannot hide them.
            scan_shared.update(direction=direction,basis=basis,tf=interval,symbol=sym,timestamp=advanced.get("timestamp"))
            if not hist.get("cached"):market_store.put("analysis",(sym,interval),scan_shared)
            scan_last_success[0]=datetime.now().timestamp()
            if current[0]==0:request_view_refresh(0)
            lines=[txt(v["name"]+" • "+("BULLISH" if v["vote"]==1 else "BEARISH" if v["vote"]==-1 else "NEUTRAL" if v["vote"]==0 else "UNAVAILABLE")+" • "+v["detail"],11,
                       GREEN if v["vote"]==1 else RED if v["vote"]==-1 else MUTED) for v in advanced["votes"]]
            support=min(float(b[3]) for b in bars[-20:])
            resistance=max(float(b[2]) for b in bars[-20:])
            budget=scan_budget.value or "80-120"
            if budget=="Custom":
                low=float(scan_min.value);high=float(scan_max.value)
            elif budget=="Any":low,high=0.,float("inf")
            else:low,high=map(float,budget.split("-"))
            if not (math.isfinite(low) and low>=0 and high>low):raise ValueError("Premium range must have a valid minimum and larger maximum.")
            days=int(scan_expiry.value or "14")
            def normal_cdf(x):return .5*(1+math.erf(x/math.sqrt(2)))
            def model(k,call,days_left):
                t=max(days_left,0.01)/365
                sig=volatility;r=.06
                d1=(math.log(price/k)+(r+.5*sig*sig)*t)/(sig*math.sqrt(t))
                d2=d1-sig*math.sqrt(t)
                if call:return max(0.,price*normal_cdf(d1)-k*math.exp(-r*t)*normal_cdf(d2))
                return max(0.,k*math.exp(-r*t)*normal_cdf(-d2)-price*normal_cdf(-d1))
            # Strike increments for stocks are not inferred from price: use illustrative grids.
            step=50 if sym=="NIFTY" else 100 if sym in ("BANKNIFTY","SENSEX") else max(1,round(price*.01))
            atm=round(price/step)*step
            pool=[]
            for i in range(-30,31):
                strike=atm+i*step
                if strike<=0:continue
                for call in (True,False):
                    premium=model(strike,call,days)
                    if premium<.05:continue
                    next_day=model(strike,call,max(1,days-1))
                    decay=max(0.,premium-next_day)
                    aligned=(direction=="BULLISH" and call) or (direction=="BEARISH" and not call)
                    # Penalize very far OTM and high daily time decay.
                    decay_pct=100*decay/max(premium,.01)
                    pool.append(dict(strike=strike,call=call,premium=premium,decay=decay,decay_pct=decay_pct,aligned=aligned,dist=abs(strike-price)/price))
            eligible=[v for v in pool if low<=v["premium"]<=high]
            if scan_auto.value and direction in ("BULLISH","BEARISH"):
                eligible.sort(key=lambda v:(not v["aligned"],v["dist"],v["decay_pct"]))
            else:eligible.sort(key=lambda v:(v["decay_pct"],v["dist"]))
            rows=[]
            for v in eligible[:3]:
                side="CE" if v["call"] else "PE"
                label="TREND-ALIGNED" if v["aligned"] else "COUNTER-TREND / CAUTION"
                rows.append(ft.Container(content=ft.Column([
                    txt(f'{sym} {v["strike"]:g} {side} • SIM ₹{v["premium"]:.2f}',14,GOLD,True),
                    txt(label,12,GREEN if v["aligned"] else MUTED,True),
                    note(f'Illustrative daily time decay ≈ ₹{v["decay"]:.2f} ({v["decay_pct"]:.1f}% of premium) if underlying/volatility stay constant.'),
                    note("Unverified strike/expiry • check broker.")
                ],spacing=6),bgcolor=PANEL2,padding=12,border_radius=10))
            age_warning=("HISTORICAL / STALE for selected timeframe" if hist.get("cached") or age_hours*3600>timeframe_spec(interval)["fresh_seconds"] or age_hours<0 else "source candle history; confirm with broker.")
            controls=[section("ANALYSIS BASIS • Candles & Filters",ft.Column([txt("Candle "+interval+" • Period "+period+" • "+str(len(bars))+" bars",12,GOLD,True),note("Analysis uses completed candles only; chart may show a forming candle."),note("Latest IST: "+updated.astimezone(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %Y %H:%M")),note(basis),*lines,note("OI/PCR/Max Pain not connected; unavailable filters never vote.")],spacing=5)),card(txt(sym+" • "+direction,19,GREEN if direction=="BULLISH" else RED if direction=="BEARISH" else GOLD,True),
                txt("Underlying historical close: ₹"+scan_num(price),15),
                txt(hist.get("source","Source")+" candle (IST): "+updated.astimezone(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %Y %H:%M"),12),
                txt("Data age: "+f"{max(0,age_hours):.1f}"+" hours • "+age_warning,12,RED if age_hours>24 else GOLD),
                txt("Selected timeframe: "+interval+" • Period: "+period+" • Move: "+f"{change:+.2f}%",12),
                txt("5-candle average: "+scan_num(ma_fast)+"  |  20-candle average: "+scan_num(ma_slow),12),
                txt("Support: "+scan_num(support)+"  |  Resistance: "+scan_num(resistance),12),
                txt("Indicative annualized volatility: "+f"{volatility*100:.1f}%",12),
                note("Rule-based scanner, not a trained AI model or calibrated probability."))]
            # Summary is a scenario calculator, never a live executable recommendation.
            fresh=(not hist.get("cached") and 0<=age_hours*3600<=timeframe_spec(interval)["fresh_seconds"])
            aligned_choices=[v for v in eligible if v["aligned"] and v["dist"]<=0.04]
            selected=aligned_choices[0] if aligned_choices else None
            if direction not in ("BULLISH","BEARISH") or not fresh or selected is None:
                reason=("Last candle is too old for this selected timeframe. Historical data only; wait for fresh data." if not fresh
                        else "No directional setup from the active filters: "+basis if direction not in ("BULLISH","BEARISH")
                        else "No suitable near-the-money, trend-aligned simulated premium matches this budget.")
                summary=section("TOP SETUP • WAIT / NO TRADE",ft.Column([
                    txt(reason,14,GOLD,True),
                    note("No entry, stop loss, target or holding-time recommendation is issued."),
                    note("Re-scan with fresh data; verify live option chain and contract with broker.")
                ],spacing=8))
            else:
                side="CE" if selected["call"] else "PE"
                entry=selected["premium"]
                # Explicitly illustrative percentage scenarios, NOT forecasted fills.
                stop=entry*0.80
                target1=entry*1.20
                target2=entry*1.35
                horizon=timeframe_spec(interval)["horizon"]
                intrinsic=max(0.0,price-selected["strike"]) if selected["call"] else max(0.0,selected["strike"]-price)
                time_value=max(0.0,entry-intrinsic)
                summary=section("TOP SETUP • SIMULATION ONLY",ft.Column([
                    txt(f'{sym} {selected["strike"]:g} {side} • modeled ₹{entry:.2f}',16,GOLD,True),
                    txt(f'Illustrative entry ₹{entry:.2f} | SL ₹{stop:.2f}',14),
                    txt(f'Illustrative targets ₹{target1:.2f} / ₹{target2:.2f}',14),
                    txt("Scenario horizon: "+horizon,13),
                    txt(f'Intrinsic ≈ ₹{intrinsic:.2f} | Time value ≈ ₹{time_value:.2f}',12),
                    note("20% stop and 20%/35% targets are fixed hypothetical scenarios, not market-derived predictions."),
                    note("Actual strike, expiry, premium, liquidity and order execution are UNVERIFIED. Do not trade from this simulation alone.")
                ],spacing=8))
            controls.insert(0,summary)
            if rows:
                controls.append(section("Premium candidates • SIMULATION ONLY",ft.Column(rows,spacing=8)))
            else:
                nearest=sorted(pool,key=lambda v:abs(v["premium"]-(low+high)/2) if math.isfinite(high) else v["dist"])[:3]
                lines=[note("No modeled contract matched this budget. Here are nearby theoretical prices; not real exchange quotes.")]
                for v in nearest:
                    lines.append(txt(f'{v["strike"]:g} {"CE" if v["call"] else "PE"} ≈ ₹{v["premium"]:.2f} (simulation)',12))
                controls.append(section("No budget match — alternatives",ft.Column(lines,spacing=7)))
            controls.append(section("Risk / validation",ft.Column([
                note("SIMULATION ONLY • Verify actual expiry, strikes, bid/ask, OI, lot size, IV and theta with a broker. Premium can decay rapidly; do not trade from modeled quotes."),
                ft.ElevatedButton("Dashboard",on_click=lambda e:select(0))
            ])))
            try:
                combined=await asyncio.wait_for(load_combined(sym,interval,advanced),timeout=20)
            except Exception as exc:
                log_error("combined_news",exc)
                missing={"items":[],"status":safe_error(exc)}
                combined=combine_analysis(sym,interval,advanced,missing,missing)
            if generation!=scan_generation[0] or sym!=scan_symbol.value or interval!=scan_tf.value:return
            fusion_cache[sym+":"+interval]=combined
            fusion_selected.controls=[fusion_card(sym,interval)]
            if not hist.get("cached"):
                scan_shared.update(direction=direction,basis=basis,tf=interval,symbol=sym,timestamp=advanced.get("timestamp"))
                market_store.put("analysis",(sym,interval),scan_shared)
            scan_result.controls=controls
            scan_last_success[0]=datetime.now().timestamp()
            scan_next_refresh[0]=(scan_last_success[0]+int(scan_refresh.value or "60")) if scan_live.value else None
            scan_status.value="Last checked "+datetime.now().strftime("%H:%M:%S")+" • source candle "+updated.strftime("%H:%M UTC")+" • updates only when source changes"
            refresh_scan_age()
        except Exception as exc:
            log_error("scanner",exc)
            if generation!=scan_generation[0]:return
            scan_status.value="Refresh failed • last results may be stale"
            if not scan_live.value or not scan_result.controls:
                scan_result.controls=[card(unavailable("Scanner: "+safe_error(exc)),note("No signal was generated. Check filters, broker connection and data availability."))]
        finally:
            scan_busy[0]=False
            refresh_scan_age()
            if generation!=scan_generation[0]:
                page.run_task(restart_latest_scan)
            if current[0]==3 and chart_provider[0]=="TradingView Lightweight":
                # Preserve the native chart while updating result/status controls.
                page.update()
            elif current[0] in (0,3):
                select(current[0])
    def bind_saved(control,key):
        field_bindings.append((control,key))
        if key in prefs:control.value=str(prefs[key]) if isinstance(control,(ft.TextField,ft.Dropdown)) else prefs[key]
        prefs.setdefault(key,control.value)
        previous=control.on_change
        def changed(e):
            if save_control(control,key):
                if isinstance(control,ft.Slider) and hasattr(control,"_bk_help_label"):
                    control._bk_help_label.value=f"Signal agreement: {control.value:g}%"
                if key in ("bot_symbol","bot_custom","bot_type","bot_strike","bot_expiry","bot_lot_size","bot_lots","bot_expiry_mode","bot_premium","bot_segment","cash_quantity"):
                    manual_contract_confirmed.value=False;prefs["manual_contract_confirmed"]=False
                ok=save();status.value="Saved automatically" if ok else "Save failed — device storage unavailable";status.color=GREEN if ok else RED
                if key.startswith("protection_"):protection_pending.clear()
                if previous is not None:previous(e)
            else:status.value="Invalid value — not saved. Fix the field below.";status.color=RED
            page.update()
        control.on_change=changed
    bindings=[(mode,"mode"),(source,"source"),(broker,"broker"),(api_url,"api_url"),
        (sl,"stop_loss"),(target,"target"),(limit,"max_trades"),(conf,"confidence"),
        (bot_symbol,"bot_symbol"),(bot_custom,"bot_custom"),(bot_type,"bot_type"),(bot_strike,"bot_strike"),
        (bot_expiry,"bot_expiry"),(bot_expiry_mode,"bot_expiry_mode"),(bot_lots,"bot_lots"),(bot_lot_size,"bot_lot_size"),(bot_premium,"bot_premium"),
        (bot_trailing,"bot_trailing"),(auto_entry,"auto_entry"),(auto_reentry,"auto_reentry"),(buy_dip,"buy_dip"),(partial_profit,"partial_profit"),
        (max_total_lots,"max_total_lots"),(dip_step,"dip_step"),(cooldown,"cooldown"),(max_daily_loss,"max_daily_loss"),(squareoff,"squareoff"),(emergency_stop,"emergency_stop"),
        (scan_symbol,"scanner_symbol"),(scan_tf,"scanner_timeframe"),(scan_budget,"scanner_budget"),(scan_min,"scanner_min"),(scan_max,"scanner_max"),
        (scan_period,"scanner_period"),(scan_expiry,"scanner_expiry"),(scan_auto,"scanner_trend"),(scan_live,"scanner_live"),(scan_refresh,"scanner_refresh"),
        (chain_symbol,"option_symbol"),(option_expiry_choice,"option_expiry_choice"),(expiry,"option_expiry"),(option_strike,"option_strike"),(option_side,"option_side"),(option_qty,"option_qty")]
    bindings.extend([(protection_mode,"protection_mode"),(protection_enabled,"protection_enabled"),(protection_loss,"protection_loss"),(protection_profit,"protection_profit"),(protection_trail,"protection_trail"),(protection_timeout,"protection_timeout"),(protection_no_reply,"protection_no_reply")])
    bindings.extend([(bot_segment,"bot_segment"),(bot_side,"bot_side"),(cash_quantity,"cash_quantity"),(cash_max_quantity,"cash_max_quantity"),(manual_contract_confirmed,"manual_contract_confirmed"),(paper_capital,"paper_capital"),(paper_notional_limit,"paper_notional_limit"),(paper_trade_risk,"paper_trade_risk"),(paper_risk_pct,"paper_risk_pct"),(paper_max_additions,"paper_max_additions"),(paper_add_units,"paper_add_units"),(paper_trail_pct,"paper_trail_pct"),(paper_partial_trigger,"paper_partial_trigger"),(paper_partial_pct,"paper_partial_pct"),(paper_reentry_after_sl,"paper_reentry_after_sl")])
    for control,key in bindings:bind_saved(control,key)
    def provider_changed(e):
        nonlocal market_status
        dhan_batch_issue[0]=None
        market_status="Data source: "+source.value+" • waiting for refresh"
        provider_generation[0]+=1
        # Preserve the last displayed price while the new provider reconnects.
        # Mark it as historical/unverified rather than implying that the old
        # provider's quote is live data from the newly selected provider.
        previous_quotes=dict(quotes)
        quotes.clear();candles.clear();fusion_cache.clear();scan_generation[0]+=1
        scan_progress.update(checked=0,total=len(watch_symbols),valid=0,failed=0,cached=0,state="Awaiting "+source.value+" candle scan")
        failed_symbols.clear()
        top5_candidates.clear()
        cached_source={"Broker API":"Angel One","Yahoo Finance":"Yahoo Finance","Dhan":"Dhan"}.get(source.value,"")
        quotes.update({sym:dict(row,freshness="unverified",live_verified=False) for sym,row in previous_quotes.items()
                       if isinstance(row,dict) and row.get("source")==cached_source
                       and isinstance(row.get("price"),(int,float))
                       and not isinstance(row.get("price"),bool) and math.isfinite(row["price"])})
        # Prefer last known snapshots from the newly selected provider.
        quotes.update({sym:row for sym,row in market_store.latest_markets().items() if row.get("source")==cached_source})
        scan_next_refresh[0]=None
        scan_result.controls.clear()
        connection_status.value=("Dhan read-only • 51 equities mapped • "+("HISTORICAL ONLY • LIVE LTP UNAVAILABLE" if dhan_feed.historical_only else "LTP verified • quote timestamp unverified" if dhan_feed.connected else "reconnect required") if source.value=="Dhan" else "Data source: "+source.value+" • "+("Angel One connected" if angel_feed.connected else "broker disconnected"))
        scan_status.value=connection_status.value
        select(current[0])
    broker_previous=broker.on_change
    def broker_changed(e):
        angel_feed.disconnect();dhan_feed.disconnect();option_feed.clear();option_snapshots.clear()
        broker_previous(e);provider_changed(e)
    broker.on_change=broker_changed
    source_previous=source.on_change
    def source_change(e):
        prefs["source"]=source.value
        source_previous(e);provider_changed(e)
    source.on_change=source_change
    pages=[dashboard,options,settings,scanner,watchlist,charts]
    icons=[ft.Icons.DASHBOARD,ft.Icons.TABLE_CHART,ft.Icons.SETTINGS,ft.Icons.SEARCH,ft.Icons.LIST,ft.Icons.CANDLESTICK_CHART]
    names=["Home","Options","Settings","Scanner","Watchlist","Chart"]
    def remember_scroll(e):
        prefs.setdefault("page_scroll",{})[str(current[0])]=max(0,float(e.pixels))
    body=ft.Column(expand=True,scroll=ft.ScrollMode.AUTO,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,spacing=12,on_scroll=remember_scroll,on_scroll_interval=750)
    navbar=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY,spacing=0,expand=True)
    current=[int(prefs.get("last_page",0)) if str(prefs.get("last_page",0)).isdigit() and 0<=int(prefs.get("last_page",0))<len(pages) else 0]
    async def restore_scroll(i):
        await asyncio.sleep(.15)
        if current[0]==i:
            try:body.scroll_to(offset=float(prefs.get("page_scroll",{}).get(str(i),0)),duration=0)
            except Exception as exc:log_error("scroll",exc)
    def language_panel():
        picker=ft.Dropdown(label="Language",dense=True,value=prefs.get("language","English"),
            options=[ft.dropdown.Option("English"),ft.dropdown.Option("हिंदी")])
        def change_language(e):
            if e.control.value not in ("English","हिंदी"):return
            prefs["language"]=e.control.value;save();select(current[0])
        picker.on_change=change_language
        return picker
    nav_items=[]
    for j in range(len(pages)):
        icon=ft.Icon(icons[j],color=MUTED,size=19)
        label=txt(names[j],9,MUTED)
        button=ft.TextButton(content=ft.Column([icon,label],horizontal_alignment=ft.CrossAxisAlignment.CENTER,spacing=2),on_click=lambda e,k=j:select(k),style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=0,vertical=6)))
        navbar.controls.append(ft.Container(content=button,expand=1))
        nav_items.append((icon,label))
    first_render=[True]
    refresh_pending=[False]
    refresh_target=[None]
    async def flush_view_refresh():
        await asyncio.sleep(.25)
        target=refresh_target[0];refresh_pending[0]=False;refresh_target[0]=None
        select(target,refresh_only=True)
    def request_view_refresh(i):
        if current[0]!=i:return
        refresh_target[0]=i
        if not refresh_pending[0]:
            refresh_pending[0]=True
            page.run_task(flush_view_refresh)
    def select(i,refresh_only=False):
        with view_lock:
            if refresh_only and current[0]!=i:return
            render_page(i)
    def render_page(i):
        changed=current[0]!=i
        try:
            # Construct the new page first; a builder error must not erase the old page.
            controls=([language_panel()] if i==2 else [note(quote_caption(chain_symbol.value if i==1 else (scan_symbol.value or "NIFTY")))])+[decorate_help(c) for c in pages[i]()]
        except Exception as exc:
            log_error("navigation",exc)
            page.open(ft.AlertDialog(title=txt("Page could not open",17,GOLD,True),content=note("A page error was recorded in Diagnostics. The previous page remains available."))) if hasattr(page,"open") else None
            return
        if changed and current[0]==3 and i!=3:
            tv_view[0]=None;tv_context[0]=None;tv_ready[0]=False;tv_booted[0]=False;tv_js_view[0]=None
        current[0]=i
        if changed:prefs["last_page"]=i;save()
        body.controls[:]=controls
        if changed and i==4 and prefs.get("source")=="Dhan" and dhan_feed.connected:
            page.run_task(refresh_watch_batch)
        if changed and i==5 and not chart_load_busy[0]:
            # A watchlist quote may carry 5m bars, but it is not necessarily
            # a loaded chart for the selected timeframe. Check the actual
            # chart snapshot key rather than suppressing the first chart load.
            chart_key=(symbol.value,timeframe.value,provider_generation[0])
            chart_snapshot=chart_snapshots.get(chart_key) or {}
            expected={"Dhan":"Dhan","Broker API":"Angel One","Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"))
            if chart_snapshot.get("source")!=expected or not chart_snapshot.get("bars"):
                page.run_task(load_chart)
        for j,(icon,label) in enumerate(nav_items):
            icon.color=GOLD if i==j else MUTED;label.color=GOLD if i==j else MUTED
        for root in page.controls:localize_tree(root,prefs.get("language","English"))
        page.update()
        if changed or first_render[0]:page.run_task(restore_scroll,i)
        first_render[0]=False
    page.add(ft.Container(content=ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS,color=GOLD,size=30),ft.Column([txt("BOT KING",19,GOLD,True),txt("v"+APP_VERSION+" • Paper mode • Live OFF",11,MUTED)],spacing=0,expand=True),ft.Icon(ft.Icons.NOTIFICATIONS_NONE,color=GOLD)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),padding=ft.padding.only(left=14,right=14,top=32,bottom=7),bgcolor=BG),ft.Container(content=body,expand=True,padding=ft.padding.symmetric(horizontal=12,vertical=5)),ft.Container(content=navbar,bgcolor="#102330",padding=ft.padding.symmetric(vertical=5)))
    select(current[0])
    page.run_task(auto_scan_loop,scan_auto_generation[0])
    page.run_task(scan_age_clock)
    page.run_task(scanner_fast_signal_loop)
    page.run_task(protection_clock)
    async def refresh_market():
        nonlocal market_status
        initial=True
        last_scanned_generation=None
        closed_session_retry_generation=None
        while True:
            # Android can report a transient inactive lifecycle state while the
            # visible app is still in use. Never strand the first authenticated
            # Dhan historical scan behind that flag; allow one generation scan.
            pending_dhan_scan=(prefs.get("source")=="Dhan" and dhan_feed.connected
                               and last_scanned_generation!=provider_generation[0])
            if not app_active[0] and (lifecycle_background[0] or not pending_dhan_scan):
                # Do not initiate a new 51-symbol history scan while Android is
                # backgrounded, even when a new Dhan generation is pending.
                # The pending generation is retained for the next foreground pass.
                if prefs.get("source")=="Dhan" and dhan_feed.connected:
                    scan_progress["state"]="Dhan scan waiting for app foreground • last completed results retained"
                await asyncio.sleep(5);continue
            # Scan historical candles once after provider changes, even on closed days.
            current_generation=provider_generation[0]
            if not initial and not regular_hours() and last_scanned_generation==current_generation:
                # Closed-market history does not change every two minutes.
                # Keep the last successful result visible until resume or reconnect.
                if prefs.get("source")=="Dhan" and scan_progress.get("state")=="Complete":
                    scan_progress["state"]="Complete • market closed; next history scan on resume or reconnect"
                await asyncio.sleep(5)
                continue
            initial=False
            # Error diagnostics are scoped to each scan cycle. Previous provider
            # failures must not survive a successful subsequent scan.
            failed_symbols.clear()
            successes=0  # Defined even when no supported market provider is selected.
            generation=current_generation
            # Mark a closed-session scan as attempted only after its provider is ready.
            # Otherwise the first disconnected launch suppresses the entire scan after login.
            if prefs.get("source") in ("Yahoo Finance","Broker API","Dhan"):
                generation=provider_generation[0]
                scan_progress["state"]="Starting historical scan • provider "+str(prefs.get("source"))
                if prefs.get("source")=="Dhan" and not dhan_feed.connected:
                    scan_progress.update(checked=0,total=len(watch_symbols),valid=0,failed=0,cached=0,state="Dhan reconnect required; scan paused")
                    if current[0] in (0,4):request_view_refresh(current[0])
                    await asyncio.sleep(3)
                    continue
                if prefs.get("source")=="Dhan" and dhan_feed.connected:
                    try:
                        scan_progress["state"]="Checking Dhan batch before historical scan"
                        # Reuse the just-verified login/watchlist batch instead of immediately
                        # issuing another Dhan request when the historical scan starts.
                        with dhan_batch_lock:
                            cached_batch = (dict(dhan_batch_cache["quotes"])
                                if dhan_batch_cache["generation"] == generation
                                and time.monotonic() - dhan_batch_cache["updated"] < 45
                                else None)
                        batch = (cached_batch if cached_batch is not None else
                            await asyncio.wait_for(asyncio.to_thread(dhan_feed.batch_quotes), timeout=20))
                        if generation==provider_generation[0] and prefs.get("source")=="Dhan":
                            with dhan_batch_lock:
                                dhan_batch_cache.update(generation=generation,
                                                        updated=time.monotonic(),quotes=batch)
                            # Watchlist LTP must not depend on historical candle success.
                            # Retain last valid prices for missing symbols; partial
                            # snapshot data is not evidence of a new live quote.
                            # Keep verified Dhan quotes distinct from stale/cross-provider data.
                            for ticker, snapshot in batch.items():
                                if ticker in all_watch_symbols() and snapshot.get("source") == "Dhan" and isinstance(snapshot.get("price"),(int,float)) and not isinstance(snapshot.get("price"),bool) and math.isfinite(snapshot["price"]):
                                    previous = quotes.get(ticker) or {}
                                    quotes[ticker] = dict(snapshot, change=None,
                                        bars=previous.get("bars", []) if previous.get("source") == "Dhan" else [],
                                        fetched_at=time.time())
                            if current[0] == 4:
                                request_view_refresh(4)
                    except Exception as exc:
                        log_error("dhan_batch",exc)
                        market_status="Dhan batch LTP unavailable: "+safe_error(exc)
                        if current[0] in (0,4):request_view_refresh(current[0])
                        with dhan_batch_lock:
                            dhan_batch_cache.update(generation=None,updated=0.0,quotes={})
                        if generation==provider_generation[0] and prefs.get("source")=="Dhan":
                            # Keep last valid Dhan prices visible on feed failure.
                            # market_status above explicitly reports unavailable LTP.
                            if current[0]==4:
                                request_view_refresh(4)
                # Connection is now ready: allow the first historical scan even on weekends.
                last_scanned_generation=current_generation
                successes=0
                symbols=(list(dict.fromkeys(["NIFTY"]+[selected for i,default in enumerate(("NIFTY","RELIANCE","HDFCBANK"),1) for selected in [prefs.get("dashboard_analysis_slot_"+str(i),default)] if selected in watch_symbols]+all_watch_symbols())) if prefs.get("source")=="Dhan" else list(dict.fromkeys([scan_symbol.value or "NIFTY","NIFTY","BANKNIFTY","SENSEX"]+all_watch_symbols())))
                # Prioritize the selected scanner symbol and previously ranked Super Five
                # before the remaining watchlist; retain full-list coverage and stable order.
                # Only verified watchlist symbols may enter the Dhan history queue.
                if prefs.get("source")=="Dhan":
                    # On cold start, prioritize the visible scanner and dashboard
                    # equities before the remaining 51-symbol history queue.
                    # The index probe remains deferred below to protect equities.
                    dashboard_priority=[prefs.get("dashboard_analysis_slot_"+str(i),default)
                                        for i,default in enumerate(("NIFTY","RELIANCE","HDFCBANK"),1)]
                    priority=[scan_symbol.value or "NIFTY"]+dashboard_priority+[row.get("symbol") for row in top5_candidates if isinstance(row,dict)]
                    symbols=list(dict.fromkeys(
                        [sym for sym in priority if sym in symbols]+symbols))
                # Probe an equity first for the fail-fast provider guard, then
                # inspect NIFTY early so its index card need not wait for 51
                # equities. NIFTY failure must not block the equity scan.
                if prefs.get("source")=="Dhan" and "NIFTY" in symbols:
                    equities=[sym for sym in symbols if sym!="NIFTY"]
                    symbols=([equities[0],"NIFTY"]+equities[1:]) if equities else ["NIFTY"]
                # Dhan candle calls are rate-sensitive; quote LTP is already batched.
                semaphore=asyncio.Semaphore(2 if prefs.get("source")=="Dhan" else 5)
                scan_progress.update(checked=0,total=len(symbols),valid=0,failed=0,cached=0,state="Loading candle histories: 0 / "+str(len(symbols)))
                market_completed=[0]
                history_failed=[0]
                history_cached=[0]
                cycle_data={}
                background_interrupted=False
                async def load_one(sym):
                    async with semaphore:
                        try:
                            # Bound each history request so one stalled symbol cannot block all 51 rankings.
                            # Dhan history is serialized and paced once between
                            # requests in the outer scan loop; avoid double sleeping.
                            data=await asyncio.wait_for(asyncio.to_thread(get_market_data,sym,"5m","2d"),timeout=25)
                            if generation!=provider_generation[0] or prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):return False
                            # Preserve the verified Dhan batch quote when historical candles refresh.
                            if prefs.get("source")=="Dhan":
                                with dhan_batch_lock:
                                    latest=dhan_batch_cache["quotes"].get(sym) if (
                                        dhan_batch_cache["generation"]==generation and
                                        time.monotonic()-dhan_batch_cache["updated"]<90) else None
                                if (latest and latest.get("source")=="Dhan" and
                                        isinstance(latest.get("price"),(int,float)) and
                                        not isinstance(latest.get("price"),bool) and
                                        math.isfinite(latest["price"]) and latest["price"]>0):
                                    data=dict(data,price=latest["price"],quote_timestamp=None,
                                              freshness="unverified",fetched_at=time.time())
                            # Historical scans must never overwrite a newer live LTP
                            # published by the independent 30-second quote poll.
                            # Keep candle data for ranking, but preserve the newest
                            # same-provider price in the displayed quote snapshot.
                            cycle_data[sym]=data
                            previous_quote=quotes.get(sym) or {}
                            previous_stamp=previous_quote.get("fetched_at")
                            data_stamp=data.get("fetched_at") if isinstance(data,dict) else None
                            if (prefs.get("source")=="Dhan"
                                    and previous_quote.get("source")=="Dhan"
                                    and isinstance(previous_stamp,(int,float))
                                    and (not isinstance(data_stamp,(int,float)) or previous_stamp>data_stamp)
                                    and isinstance(previous_quote.get("price"),(int,float))
                                    and not isinstance(previous_quote.get("price"),bool)
                                    and math.isfinite(previous_quote["price"]) and previous_quote["price"]>0):
                                quotes[sym]=dict(data,price=previous_quote["price"],
                                                 fetched_at=previous_stamp,source="Dhan",
                                                 quote_timestamp=previous_quote.get("quote_timestamp"),
                                                 freshness=previous_quote.get("freshness","unverified"),
                                                 change=previous_quote.get("change"))
                            else:
                                quotes[sym]=data
                            market_completed[0]+=1
                            history_cached[0]+=int(bool(data.get("cached")))
                            scan_progress["state"]="Loading histories: "+str(market_completed[0])+" / "+str(len(symbols))+" • "+str(history_failed[0])+" failed • "+str(history_cached[0])+" cached"+(" • first: "+next(iter(failed_symbols.items()))[0]+": "+next(iter(failed_symbols.values()))[:75] if failed_symbols else "")+"; ranking follows"
                            if current[0] in (0,4,5) and market_completed[0]%5==0:request_view_refresh(current[0])
                            return not data.get("cached")
                        except Exception as exc:
                            # Android may suspend network work mid-request when the
                            # user answers a call or opens another app. Do not turn
                            # lifecycle interruption into a failed market symbol.
                            if not app_active[0] or generation!=provider_generation[0]:
                                return False
                            if generation==provider_generation[0]:
                                failed_symbols[sym]=safe_error(exc)
                                history_failed[0]+=1
                                market_completed[0]+=1
                                scan_progress["state"]="Loading histories: "+str(market_completed[0])+" / "+str(len(symbols))+" • "+str(history_failed[0])+" failed"+(" • first: "+next(iter(failed_symbols.items()))[0]+": "+next(iter(failed_symbols.values()))[:75] if failed_symbols else "")+"; ranking follows"
                                if current[0] in (0,4,5):request_view_refresh(current[0])
                            return False
                # Fail fast on a broken Dhan history endpoint. One representative
                # candle failure must not trigger another 50 doomed API calls.
                if prefs.get("source")=="Dhan" and symbols:
                    # Batch quote lookup can finish after Android backgrounds the
                    # app. Avoid even the first rate-sensitive history request.
                    if lifecycle_background[0]:
                        scan_progress["state"]="Dhan history waiting for foreground • last ranking retained"
                        last_scanned_generation=None
                        await asyncio.sleep(5)
                        continue
                    first_ok=await load_one(symbols[0])
                    if not first_ok and symbols[0] in failed_symbols:
                        reason=failed_symbols[symbols[0]]
                        scan_progress.update(checked=1,total=len(symbols),valid=0,
                                             failed=1,state="Dhan historical feed unavailable • scan paused • 1 failed • "+str(max(0,len(symbols)-1))+" not attempted • first error: "+reason[:110])
                        market_status="Dhan candle history unavailable • "+reason[:110]+" • equity LTP remains separate"
                        if current[0] in (0,4,5):request_view_refresh(current[0])
                        # Honor the actual Dhan 429 retry window before probing
                        # historical candles again; preserve all saved quotes.
                        # Keep the generation pending: a failed cold-start probe
                        # must retry after cooldown even when the market is closed.
                        last_scanned_generation=None
                        await asyncio.sleep(max(30, dhan_feed.cooldown_remaining("/dhan/intraday")))
                        continue
                    results=[first_ok]
                    # Dhan history is a rate-limited upstream API: serialize
                    # calls and stop this cycle when its cooldown is triggered.
                    for sym in symbols[1:]:
                        if generation!=provider_generation[0] or not dhan_feed.connected:
                            break
                        # Android can move to background during a 51-symbol scan.
                        # Keep its generation pending; do not issue more history
                        # requests until foreground, even after the pacing sleep.
                        if lifecycle_background[0]:
                            scan_progress["state"]="Dhan historical scan paused in background • resume to continue"
                            last_scanned_generation=None
                            background_interrupted=True
                            break
                        if any("rate limited" in err.lower() or "cooldown" in err.lower()
                               for err in failed_symbols.values()):
                            scan_progress["state"]="Dhan historical scan paused after HTTP 429 • waiting for provider cooldown"
                            break
                        # The 1.5s pacing protects real upstream history calls.
                        # A recent same-generation cached history needs no API
                        # request and should not incur that network pacing delay.
                        history_key=(generation,angel_feed.epoch,dhan_feed.connected,
                                     prefs.get("source","Dhan"),sym,"5m","2d")
                        with market_registry_lock:
                            cached_history=market_recent.get(history_key)
                            cache_ready=bool(cached_history and
                                time.monotonic()-cached_history[0]<87)
                        if not cache_ready:
                            await asyncio.sleep(1.5)
                        if lifecycle_background[0]:
                            scan_progress["state"]="Dhan historical scan paused in background • resume to continue"
                            last_scanned_generation=None
                            background_interrupted=True
                            break
                        results.append(await load_one(sym))
                else:
                    results=await asyncio.gather(*(load_one(sym) for sym in symbols))
                # A background-interrupted Dhan pass is incomplete. Do not
                # replace the last good Super Five ranking with partial results.
                # The pending generation is retried after foreground resume.
                if prefs.get("source")=="Dhan" and (lifecycle_background[0] or background_interrupted):
                    scan_progress["state"]="Dhan historical scan paused in background • last ranking retained"
                    last_scanned_generation=None
                    await asyncio.sleep(5)
                    continue
                if generation!=provider_generation[0] or prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):
                    await asyncio.sleep(.05)
                    continue
                # A provider cooldown is not 51 individual candle failures. Do not
                # rank unrequested symbols or overwrite last-good Super Five results.
                if prefs.get("source")=="Dhan" and any(
                    "rate limited" in reason.lower() or "cooldown" in reason.lower()
                    or "http 429" in reason.lower() for reason in failed_symbols.values()
                ):
                    scan_progress.update(checked=market_completed[0],total=len(symbols),
                        valid=0,failed=history_failed[0],cached=0,
                        state="Dhan historical scan paused: HTTP 429 / cooldown; "
                              +str(max(0,len(symbols)-market_completed[0]))+" symbols not attempted")
                    market_status="Dhan LTP remains available; candle scan paused by provider cooldown"
                    if current[0] in (0,4,5):request_view_refresh(current[0])
                    # An incomplete rate-limited pass is not a completed generation.
                    # Otherwise the closed-market guard suppresses every retry.
                    last_scanned_generation=None
                    await asyncio.sleep(max(60, dhan_feed.cooldown_remaining("/dhan/intraday")))
                    continue
                successes=sum(results)
                # Index histories are separate from the 51-equity scanner total.
                # Reuse NIFTY already fetched in this scan; fetch BANKNIFTY and
                # SENSEX serially only after the equity pass and without fanout.
                if (prefs.get("source")=="Dhan" and dhan_feed.connected
                        and generation==provider_generation[0] and app_active[0]
                        and dhan_feed.cooldown_remaining("/dhan/intraday")==0):
                    for index_sym in ("NIFTY","BANKNIFTY","SENSEX"):
                        if generation!=provider_generation[0] or lifecycle_background[0]:
                            break
                        try:
                            if index_sym in cycle_data:
                                index_history=cycle_data[index_sym]
                            else:
                                if dhan_feed.cooldown_remaining("/dhan/intraday")>0:
                                    break
                                await asyncio.sleep(1.5)
                                index_history=await asyncio.wait_for(
                                    asyncio.to_thread(get_market_data,index_sym,"5m","2d"),
                                    timeout=25)
                            if (index_history.get("source")=="Dhan"
                                    and index_history.get("bars")
                                    and generation==provider_generation[0]):
                                chart_snapshots[(index_sym,"5m",generation)]=dict(
                                    index_history,_scanner_timeframe="5m")
                                if current[0] in (0,4):
                                    request_view_refresh(current[0])
                        except Exception as exc:
                            log_error("index_candle_"+index_sym,exc)
                            if ("429" in safe_error(exc) or
                                    dhan_feed.cooldown_remaining("/dhan/intraday")>0):
                                break
                cached_histories=sum(bool(data.get("cached") and data.get("bars")) for data in cycle_data.values())
                if successes:
                    market_status=f"{prefs.get('source','Dhan')} • {successes} candle histories updated"+(f" • {cached_histories} saved histories" if cached_histories else "")+" • "+datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime("%H:%M IST")
                elif prefs.get("source")=="Dhan" and dhan_feed.connected:
                    with dhan_batch_lock:
                        batch_count=len(dhan_batch_cache["quotes"]) if dhan_batch_cache["generation"]==generation else 0
                    market_status=("Dhan • "+str(cached_histories)+" saved candle histories; no fresh histories fetched • "+str(batch_count)+" equity LTP quotes"
                                   if cached_histories else
                                   "Dhan • "+str(batch_count)+" equity LTP quotes; historical candles unavailable"
                                   if batch_count else "Dhan • LTP and candle data unavailable; check server diagnostics")
                else:
                    market_status="Data unavailable • "+next(iter(failed_symbols.values()),"No successful response")
                # Do not classify a disconnected Dhan feed as 51 failed symbols.
                if prefs.get("source")=="Dhan" and not dhan_feed.connected:
                    scan_progress.update(checked=0,total=len(watch_symbols),valid=0,
                                         failed=0,cached=0,state="Dhan reconnect required; scan paused")
                    if current[0] in (0,4):request_view_refresh(current[0])
                    await asyncio.sleep(15)
                    continue
                # Fresh candle-only Top 5; scan across the watchlist and include indexes.
                ranking_results={}
                scan_progress.update(checked=0,total=len(watch_symbols),valid=0,failed=0,cached=0,state="Ranking completed candles: 0 / "+str(len(watch_symbols))+" • "+str(history_failed[0])+" history fetch failures")
                async def rank_one(sym):
                    async with semaphore:
                        data=None;result=None
                        try:
                            data=cycle_data.get(sym)
                            if data is None:
                                # Do not repeat a failed Dhan history call during ranking.
                                if prefs.get("source") == "Dhan":
                                    raise FeedError("Dhan history failed in first pass; use Retry")
                                data=await asyncio.to_thread(get_market_data,sym,"5m","5d")
                            result=display_analysis(sym,data)
                        except Exception as exc:
                            log_error("super_five",exc)
                            if generation==provider_generation[0] and sym not in failed_symbols:
                                failed_symbols[sym]=safe_error(exc)
                        if generation!=provider_generation[0]:return sym,None
                        ranking_results[sym]=result
                        if result and result.get("timestamp"):watch_signal_cache[sym]=dict(result,symbol=sym)
                        if result and result.get("timestamp"):failed_symbols.pop(sym,None)
                        elif sym not in failed_symbols:failed_symbols[sym]="Insufficient completed candles"
                        scan_progress["checked"]+=1
                        scan_progress["valid"]+=int(bool(result and result.get("timestamp")))
                        scan_progress["failed"]+=int(not bool(result and result.get("timestamp")))
                        scan_progress["cached"]+=int(bool(data and data.get("cached")))
                        # Publish completed Dhan candle votes in groups of five.
                        # No additional broker request is made here: ranking uses
                        # the already collected candle data from this scan.
                        if prefs.get("source")!="Dhan" or scan_progress["checked"]%5==0:
                            publish_partial_ranking(ranking_results)
                            if current[0] in (0,4):request_view_refresh(current[0])
                        return sym,result
                pairs=await asyncio.gather(*(rank_one(sym) for sym in watch_symbols))
                if generation!=provider_generation[0] or prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):
                    await asyncio.sleep(.05)
                    continue
                available=publish_partial_ranking(ranking_results)
                scan_progress["state"]="Complete" if scan_progress["valid"] else "No valid data; last saved results retained"
                async def enrich(candidate):
                    async with semaphore:
                        try:combined=await asyncio.wait_for(load_combined(candidate["symbol"],"5m",candidate),timeout=20)
                        except Exception as exc:
                            log_error("ranking_news",exc)
                            missing={"items":[],"status":safe_error(exc)}
                            combined=combine_analysis(candidate["symbol"],"5m",candidate,missing,missing)
                        return candidate,combined
                enriched=await asyncio.gather(*(enrich(candidate) for candidate in top5_candidates[:] if candidate.get("timestamp")))
                if generation!=provider_generation[0] or prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):continue
                for candidate,combined in enriched:
                    fusion_cache[candidate["symbol"]+":5m"]=combined
                    candidate.update(combined_bias=combined["overall"],coverage=combined["coverage"])
                top5_last_update[0]=datetime.now().strftime("%d %b %H:%M")
                if available:
                    market_store.put("ranking",("configured51",),{"rows":top5_candidates,"all_rows":list(watch_signal_cache.values()),"checked_at":top5_last_update[0]})
                try:
                    if current[0] in (0,1,4,5):request_view_refresh(current[0])
                except Exception:pass
            # On a closed session, one transient all-symbol failure should not
            # strand the scanner until the user reconnects. Retry only once per
            # provider generation after a 3-minute cooldown; never loop rapidly
            # over 51 rate-sensitive Dhan history endpoints.
            if (prefs.get("source")=="Dhan" and dhan_feed.connected
                    and not regular_hours() and successes==0
                    and not any("rate limited" in reason.lower() or "cooldown" in reason.lower()
                                or "http 429" in reason.lower() for reason in failed_symbols.values())
                    and closed_session_retry_generation!=generation):
                closed_session_retry_generation=generation
                scan_progress["state"]="No fresh histories • one automatic retry in 3 minutes"
                # Check for foreground reconnects/provider changes during the
                # cooldown instead of blocking their new scan for 3 minutes.
                for _ in range(36):
                    if (provider_generation[0]!=generation or prefs.get("source")!="Dhan"
                            or not dhan_feed.connected):
                        break
                    await asyncio.sleep(5)
                if (provider_generation[0]==generation and prefs.get("source")=="Dhan"
                        and dhan_feed.connected):
                    last_scanned_generation=None
            else:
                # 5-minute Dhan candles do not justify a full 51-symbol
                # historical request cycle every 120 seconds. Quotes and
                # Super Five cached analysis have independent fast refreshes.
                # Check generation every 5s so reconnect/resume is not delayed.
                wait_seconds=300 if prefs.get("source")=="Dhan" else 120
                for _ in range(wait_seconds//5):
                    if provider_generation[0]!=generation:
                        break
                    await asyncio.sleep(5)
    async def supervised_market_refresh():
        # A single unhandled exception must not permanently stop all 51 scans.
        while True:
            try:
                await refresh_market()
                log_error("market_loop_exit",RuntimeError("Market refresh task exited unexpectedly"))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log_error("market_loop_crash",exc)
            scan_progress.update(checked=0,total=len(watch_symbols),valid=0,
                                 failed=0,cached=0,state="Market scan task restarting after error; see diagnostics")
            if current[0] in (0,4):
                try:request_view_refresh(current[0])
                except Exception:pass
            await asyncio.sleep(5)
    page.run_task(supervised_market_refresh)
    page.run_task(dhan_quote_poll)
    page.run_task(watch_visible_tick)
    page.run_task(super_five_minute_refresh)
    page.run_task(option_poll)
    async def refresh_after_resume():
        if resume_busy[0]:return
        resume_busy[0]=True
        generation=provider_generation[0];sym=scan_symbol.value or "NIFTY"
        scan_next_refresh[0]=None
        try:
            # Resume the fast shared quote path before expensive candle history.
            # The background poll is suspended, so waiting up to 45 seconds
            # for its next tick unnecessarily delays the visible watchlist.
            if app_active[0] and prefs.get("source")=="Dhan" and dhan_feed.connected:
                await asyncio.sleep(10)
                if (app_active[0] and generation==provider_generation[0]
                        and time.monotonic()-quote_auto_last_attempt[0]>=30
                        and not watch_batch_busy[0] and not index_refresh_busy[0]):
                    quote_auto_last_attempt[0]=time.monotonic()
                    if dhan_feed.cooldown_remaining("/v2/snapshot")==0:
                        await refresh_watch_batch()
                    # A cooling-down equity snapshot must not suppress index recovery.
                    await refresh_dhan_index_quotes()
            if not app_active[0] or generation!=provider_generation[0]:
                return
            if current[0]==1:await refresh_selected_options()
            else:
                data=await asyncio.to_thread(get_market_data,sym,scan_tf.value or "5m",scan_period.value or "7d")
                if generation==provider_generation[0] and sym==scan_symbol.value:
                    # Resume's historical chart fetch must not replace a newer
                    # Dhan batch LTP with an older/unverified candle snapshot.
                    previous=quotes.get(sym) or {}
                    previous_dhan_price=(prefs.get("source")=="Dhan"
                                         and previous.get("source")=="Dhan"
                                         and isinstance(previous.get("price"),(int,float))
                                         and not isinstance(previous.get("price"),bool)
                                         and math.isfinite(previous["price"])
                                         and previous["price"]>0)
                    if previous_dhan_price:
                        # Resume fetches candles, not an independently verified
                        # live LTP. Preserve the last valid batch quote even when
                        # the candle response has a newer fetched_at timestamp.
                        verified_bars=(data.get("bars") if data.get("source")=="Dhan"
                                       and isinstance(data.get("bars"),list) else None)
                        quotes[sym]=dict(previous,bars=verified_bars if verified_bars is not None
                                         else previous.get("bars",[]),freshness="unverified")
                    else:
                        quotes[sym]=data
                if current[0]==5:
                    chart_sym=symbol.value
                    chart_tf=timeframe.value
                    chart_data=await asyncio.to_thread(get_market_data,chart_sym,chart_tf,"5d" if chart_tf in ("1m","5m","15m") else "1mo")
                    if generation==provider_generation[0] and chart_sym==symbol.value and chart_tf==timeframe.value:chart_snapshots[(chart_sym,chart_tf,generation)]=chart_data
            if generation==provider_generation[0] and app_active[0]:
                runtime_status.value="App resumed • selected data checked • no automatic broker order"
                select(current[0])
        except Exception as exc:
            log_error("resume",exc)
            runtime_status.value="App resumed • refresh failed; last saved data remains visible"
            page.update()
        finally:resume_busy[0]=False
    def lifecycle_changed(e):
        # Flet lifecycle events differ across Android/Flet versions: the state
        # may be in e.state, e.data, or directly in an enum/string payload.
        raw=getattr(e,"state",None)
        if raw is None:raw=getattr(e,"data",None)
        if raw is None:raw=e
        state=str(getattr(raw,"value",raw)).strip().lower()
        # Only known background states pause tasks. Unknown events are ignored
        # rather than leaving the scanner disabled or recording a false crash.
        if state=="resumed" or state.endswith(".resumed"):
            # Duplicate Android RESUMED callbacks must not restart the entire
            # 51-symbol candle scan or invalidate an in-flight provider generation.
            if app_active[0]:
                return
            app_active[0]=True
            lifecycle_background[0]=False
        elif state=="inactive" or state.endswith(".inactive"):
            # Android briefly enters inactive during overlays and focus changes.
            # Only a confirmed background/hidden state should suspend scanning.
            return
        elif state in ("paused","detached","hidden") or any(state.endswith("."+v) for v in ("paused","detached","hidden")):
            app_active[0]=False
            lifecycle_background[0]=True
        else:
            return
        if not app_active[0]:
            protection_pending.clear()
            if paper_bot_state[0]=="Running":paper_bot_state[0]="Paused";paper_state_status.value="Paper bot paused on background; press Start after returning"
            runtime_status.value="App backgrounded • uninterrupted monitoring unavailable • refresh on resume"
        else:
            runtime_status.value="App resumed • checking selected data..."
            # Resume reuses the existing authenticated session and candle cache.
            # Do not invalidate the provider generation or restart a 51-symbol
            # historical scan on every screen unlock; the regular scan timer
            # controls history refresh and the resume task checks quotes.
            if prefs.get("source")=="Dhan" and dhan_feed.connected:
                scan_progress["state"]="Dhan resumed • checking cached quotes"
            page.run_task(refresh_after_resume)
        page.update()
    page.on_app_lifecycle_state_change=lifecycle_changed

def main(page: ft.Page):
    try:
        app_main(page)
    except Exception:
        error=traceback.format_exc()
        print("BOT KING STARTUP ERROR:"+error,flush=True)
        page.controls.clear()
        page.bgcolor="#03080E"
        page.padding=16
        page.add(
            ft.Text("BOT KING — Startup Error",size=22,color="#FFCB12",weight=ft.FontWeight.BOLD),
            ft.Text("The app could not initialize. Please send a screenshot of this error.",color="#FFFFFF"),
            ft.Column([ft.Text(error,size=11,color="#FF8796",selectable=True)],scroll=ft.ScrollMode.AUTO,expand=True),
        )
        page.update()

ft.app(target=main)




