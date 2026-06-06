<template>
  <!-- ═══ 项目列表页（无打开项目时） ═══ -->
  <div v-if="!proj" class="min-h-screen bg-[#0a0a0f] text-white">
    <header class="h-14 border-b border-white/[0.06] px-5 flex items-center justify-between shrink-0 bg-[#0a0a0f]/80 backdrop-blur-sm">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/workspace')" class="text-white/40 hover:text-white transition">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <h1 class="text-sm font-semibold tracking-wide">一键成片</h1>
      </div>
      <button @click="showCreate = true" class="h-8 px-4 bg-[#7c3aed] hover:bg-[#6d28d9] rounded-lg text-xs font-medium transition">
        + 新建项目
      </button>
    </header>

    <div class="max-w-5xl mx-auto p-8">
      <div v-if="loading" class="text-center py-20 text-white/30 text-sm">加载中...</div>
      <div v-else-if="projects.length === 0" class="text-center py-20">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
          <svg class="w-7 h-7 text-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
        </div>
        <p class="text-white/30 text-sm mb-4">还没有项目</p>
        <button @click="showCreate = true" class="px-5 py-2.5 bg-[#7c3aed] hover:bg-[#6d28d9] rounded-lg text-sm font-medium transition">创建第一个项目</button>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="p in projects" :key="p.id"
          class="group bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 hover:border-[#7c3aed]/40 hover:bg-white/[0.03] transition-all cursor-pointer"
          @click="openProject(p)">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-medium text-sm truncate group-hover:text-[#a78bfa] transition">{{ p.name }}</h3>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="phaseClass(p.phase)">{{ phaseLabel(p.phase) }}</span>
          </div>
          <div class="text-xs text-white/30 space-y-0.5">
            <p>{{ p.video_model }} · {{ p.ratio }} · {{ p.segments_count ? p.segments_count + '段×' + p.duration + 's=' + (p.segments_count * p.duration) + 's' : p.duration + 's/段' }}</p>
            <div class="flex gap-1.5 mt-1.5">
              <span v-if="p.assets_count" class="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400/70">{{ p.phase2_done || 0 }}/{{ p.assets_count }} 资产</span>
              <span v-if="p.segments_count" class="px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400/70">{{ p.phase3_done || 0 }}/{{ p.segments_count }} 故事板</span>
              <span v-if="p.segments_count" class="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400/70">{{ p.phase4_done || 0 }}/{{ p.segments_count }} 视频</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 新建项目弹窗 ═══ -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="showCreate = false">
      <div class="bg-[#12121a] border border-white/[0.06] rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-base font-semibold mb-5">新建项目</h2>
        <div class="space-y-3">
          <div>
            <label class="lbl">项目名称</label>
            <input v-model="createForm.name" class="inp" placeholder="例：五旬老太重生记 Ep1" />
          </div>
          <div>
            <label class="lbl">原始剧本 <span class="text-white/15">（可选，粘贴或上传txt）</span></label>
            <div class="flex gap-2 items-start">
              <textarea v-model="createForm.raw_script" class="inp flex-1 resize-none" rows="5" placeholder="粘贴剧本内容..."></textarea>
              <label class="shrink-0 h-[104px] flex flex-col items-center justify-center bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 cursor-pointer hover:border-[#7c3aed]/30 transition">
                <svg class="w-4 h-4 text-white/20 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                <span class="text-[10px] text-white/20">上传</span>
                <input type="file" accept=".txt,.md,.text" class="hidden" @change="uploadScript" />
              </label>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl">视频模型</label><select v-model="createForm.video_model" class="sel">
              <option value="Gemini Omni">Gemini Omni</option><option value="Grok Imagine">Grok Imagine</option>
              <option value="Vidu Q3 Pro">Vidu Q3 Pro</option><option value="Kling 2.6">Kling 2.6</option>
              <option value="Wan2.7">Wan2.7</option><option value="Seedance 1.5 Pro">Seedance 1.5 Pro</option>
            </select></div>
            <div><label class="lbl">图片模型</label><select v-model="createForm.image_model" class="sel">
              <option value="GPT-Image2">GPT Image 2</option><option value="Seedream 5.0">Seedream 5.0</option>
              <option value="Flux">Flux</option><option value="Niji7">Niji7</option>
            </select></div>
          </div>
          <div class="grid grid-cols-4 gap-3">
            <div><label class="lbl">比例</label><select v-model="createForm.ratio" class="sel">
              <option value="16:9">16:9</option><option value="9:16">9:16</option><option value="1:1">1:1</option>
            </select></div>
            <div><label class="lbl">视频分辨率</label><select v-model="createForm.resolution" class="sel">
              <option value="720p">720p</option><option value="1080p">1080p</option><option value="4K">4K</option>
            </select></div>
            <div><label class="lbl">图片分辨率</label><select v-model="createForm.image_resolution" class="sel">
              <option value="1K">1K</option><option value="2K">2K</option><option value="4K">4K</option>
            </select></div>
            <div><label class="lbl">时长/段</label><select v-model="createForm.duration" class="sel">
              <option :value="5">5s</option><option :value="6">6s</option><option :value="8">8s</option><option :value="10">10s</option>
            </select></div>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5">
          <button @click="showCreate = false" class="px-4 py-2 text-xs text-white/40 hover:text-white transition">取消</button>
          <button @click="createProject" class="px-5 py-2 bg-[#7c3aed] hover:bg-[#6d28d9] rounded-lg text-xs font-medium transition" :disabled="!createForm.name || creating">
            {{ creating ? '...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══ 项目详情页：左右并排布局 ═══ -->
  <div v-else class="h-screen flex flex-col bg-[#08080d] text-white/80">
    <!-- 顶栏 -->
    <div class="h-10 shrink-0 flex items-center gap-3 px-4 border-b border-white/[0.04] bg-[#08080d]">
      <button @click="closeProject" class="text-white/30 hover:text-white/60 text-xs">← 返回</button>
      <span class="text-xs font-semibold truncate max-w-[200px]">{{ proj.name }}</span>
      <button @click="scriptModal=true" class="px-2 py-0.5 text-[10px] text-white/30 hover:text-white/60 bg-white/[0.04] rounded">剧本</button>
      <div class="flex-1"></div>
      <button @click="saveScript" class="px-2 py-0.5 text-[10px] text-white/30 hover:text-white/60 bg-white/[0.04] rounded" :disabled="savingScript">{{ savingScript ? '...' : '保存' }}</button>
      <span v-if="saveNotification" class="text-[10px] text-emerald-400/70 animate-pulse">{{ saveNotification }}</span>
      <button @click="deleteProject" class="px-2 py-0.5 text-[10px] text-red-400/40 hover:text-red-400 bg-white/[0.04] rounded">删除</button>
      <button @click="showAgent=!showAgent" class="px-2 py-0.5 text-[10px] bg-white/[0.04] rounded" :class="showAgent?'text-violet-400':'text-white/30'">💬Agent</button>
    </div>

    <!-- 工作流进度条 -->
    <div class="h-9 shrink-0 flex items-center gap-1 px-4 border-b border-white/[0.04] bg-[#08080d]">
      <div v-for="(step, idx) in workflowSteps" :key="idx" class="flex items-center gap-1">
        <div v-if="idx > 0" class="w-4 h-px" :class="step.status==='pending'?'bg-white/[0.06]':'bg-emerald-500/40'"></div>
        <div class="flex items-center gap-1 px-2 py-0.5 rounded" :class="step.status==='done'?'bg-emerald-500/10':step.status==='running'?'bg-violet-500/10':'bg-white/[0.02]'">
          <span class="w-4 h-4 rounded-full text-[8px] font-bold flex items-center justify-center shrink-0"
            :class="step.status==='done'?'bg-emerald-500/30 text-emerald-400':step.status==='running'?'bg-violet-500/30 text-violet-400':'bg-white/[0.06] text-white/20'">
            <template v-if="step.status==='done'">✓</template><template v-else>{{ idx+1 }}</template>
          </span>
          <span class="text-[9px] font-medium" :class="step.status==='done'?'text-emerald-400/70':step.status==='running'?'text-violet-400/70':'text-white/25'">{{ step.label }}</span>
          <button v-if="step.action && step.status!=='done'" @click="step.actionFn" class="text-[8px] px-1 py-0.5 rounded bg-violet-500/20 text-violet-400/80 hover:bg-violet-500/30 transition shrink-0" :disabled="step.actionDisabled">{{ step.actionDisabled?'...':step.action }}</button>
        </div>
      </div>
    </div>

    <!-- 主内容区：四列并排 -->
    <div class="flex-1 flex min-h-0">

      <!-- ─── 资产列 ─── -->
      <div class="flex flex-col border-r border-white/[0.04] transition-all" :style="{width: assetCollapsed ? '48px' : '20%'}">
        <div class="px-2 py-2 flex items-center justify-between border-b border-white/[0.04]">
          <span v-if="!assetCollapsed" class="text-[11px] font-semibold text-white/40 uppercase tracking-wider">资产 ({{editAssets.length}})</span>
          <div v-if="!assetCollapsed" class="flex gap-1">
            <button v-if="editAssets.length" @click="generateAllAssets" class="text-[9px] text-violet-400/50 hover:text-violet-300" :disabled="generatingAllAssets">{{ generatingAllAssets?'生成中...':'全部生成' }}</button>
            <button @click="addAsset" class="text-[9px] text-white/20 hover:text-white/40">+</button>
            <button @click="assetCollapsed=!assetCollapsed" class="text-[10px] text-white/30 hover:text-white/60">◂</button>
          </div>
          <button v-if="assetCollapsed" @click="assetCollapsed=!assetCollapsed" class="text-[10px] text-white/30 hover:text-white/60">▸</button>
        </div>
        <div v-if="!assetCollapsed" class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-for="(a, i) in editAssets" :key="'a'+i"
               class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition group">
            <!-- 缩略图 40x40 -->
            <div class="w-10 h-10 shrink-0 rounded bg-black/30 cursor-pointer relative"
                 @click="uploadAssetRef(i)">
              <img v-if="a.reference_image || getAssetResultImage(i)"
                   :src="getUrl(a.reference_image || getAssetResultImage(i))"
                   class="w-full h-full object-cover rounded"
                   @mouseenter="showPreview(a.reference_image || getAssetResultImage(i), $event)"
                   @mouseleave="hidePreview()"
                   @mousemove="showPreview(a.reference_image || getAssetResultImage(i), $event)" />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg class="w-4 h-4 text-white/10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4"/></svg>
              </div>
              <div v-if="isAssetGenerating(i)" class="absolute inset-0 bg-black/50 flex items-center justify-center rounded">
                <div class="dot-spin"></div>
              </div>
              <div v-if="getAssetResultImage(i)" class="absolute top-0 right-0 w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
              <input type="file" :ref="(el:any) => assetFileInputs[i] = el" class="hidden" accept="image/*" @change="handleAssetRefUpload($event, i)" />
            </div>
            <!-- 信息 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1">
                <input v-model="a.name" class="bg-transparent text-[11px] font-medium flex-1 min-w-0 focus:outline-none truncate" placeholder="资产名" />
                <select v-model="a.type" class="text-[8px] bg-white/[0.04] rounded px-0.5 py-0 text-white/30 focus:outline-none shrink-0">
                  <option value="角色">角色</option><option value="场景">场景</option><option value="道具">道具</option>
                </select>
                <span v-if="a.type==='角色' && a.is_primary===false" class="text-[7px] px-1 py-0 rounded-full bg-amber-500/15 text-amber-400/80 shrink-0">衍生</span>
              </div>
              <!-- 角色多形态字段 -->
              <div v-if="a.type==='角色'" class="flex items-center gap-1 mt-0.5">
                <label class="flex items-center gap-0.5 cursor-pointer shrink-0">
                  <input type="checkbox" v-model="a.is_primary" class="w-2 h-2 accent-violet-500" />
                  <span class="text-[8px] text-white/25">主形态</span>
                </label>
                <select v-if="a.is_primary===false" v-model="a.reference_form" class="text-[8px] bg-white/[0.04] rounded px-0.5 py-0 text-white/30 focus:outline-none flex-1 min-w-0">
                  <option value="">选择参考</option>
                  <option v-for="pa in getPrimaryCharacters(i)" :key="pa.name" :value="pa.name">{{ pa.name }}</option>
                </select>
              </div>
              <div class="flex items-center gap-1 mt-0.5">
                <button @click="generateSingleAsset(i)" class="text-[9px] text-violet-400/60 hover:text-violet-300" :disabled="isAssetGenerating(i)||generatingAsset">{{ isAssetGenerating(i)||generatingAsset?'...':'生成' }}</button>
                <button @click="uploadAssetResult(i)" class="text-[9px] text-white/20 hover:text-white/40">上传</button>
                <button v-if="getAssetPrompt(i)" @click="showPromptDetail(getAssetPrompt(i))" class="text-[9px] text-white/15 hover:text-white/30">prompt</button>
                <button @click="confirmDeleteAsset(i)" class="text-[9px] text-white/15 hover:text-red-400 ml-auto">x</button>
              </div>
            </div>
          </div>
          <div v-if="!editAssets.length" class="text-center py-6 text-white/15 text-[10px]">暂无资产，点击 + 添加</div>
        </div>
        <div v-else class="flex-1 flex flex-col items-center pt-2 space-y-1">
          <span class="text-[9px] text-white/20 writing-vertical">{{ editAssets.length }}资产</span>
        </div>
      </div>

      <!-- ─── 分镜列 ─── -->
      <div class="flex flex-col border-r border-white/[0.04]" style="width:25%">
        <div class="px-3 py-2 flex items-center justify-between border-b border-white/[0.04]">
          <span class="text-[11px] font-semibold text-white/40 uppercase tracking-wider">分镜 ({{editSegments.length}}段)</span>
          <div class="flex gap-1">
            <button v-if="editSegments.length" @click="generateAllStoryboards" class="text-[9px] text-violet-400/50 hover:text-violet-300" :disabled="generatingAllStoryboards">{{ generatingAllStoryboards?'生成中...':'全部故事板' }}</button>
            <button @click="addSegment" class="text-[9px] text-white/20 hover:text-white/40">+</button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-for="(seg, si) in editSegments" :key="'s'+si"
               class="rounded-lg bg-white/[0.02] border border-white/[0.04] overflow-hidden">
            <!-- 段头部 一行 -->
            <div class="flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-white/[0.01]" @click="seg._open=!seg._open">
              <svg class="w-2.5 h-2.5 text-white/20 transition-transform shrink-0" :class="seg._open?'rotate-90':''" fill="currentColor" viewBox="0 0 20 20"><path d="M6 4l8 6-8 6V4z"/></svg>
              <input v-model="seg.title" class="bg-transparent text-[11px] font-medium flex-1 focus:outline-none" placeholder="段标题" @click.stop />
              <span class="text-[9px] text-white/20 shrink-0">{{ seg.shots?.length||0 }}镜</span>
              <!-- 故事板缩略图 -->
              <div v-if="getSegStoryboardImage(si)" class="w-8 h-6 rounded border border-white/[0.06] shrink-0 overflow-hidden">
                <img :src="getUrl(getSegStoryboardImage(si))" class="w-full h-full object-cover"
                     @mouseenter="showPreview(getSegStoryboardImage(si), $event)"
                     @mouseleave="hidePreview()"
                     @mousemove="showPreview(getSegStoryboardImage(si), $event)" />
              </div>
              <span v-if="getSegStoryboardStatus(si)" class="text-[8px] shrink-0" :class="getSegStoryboardStatus(si)==='completed'?'text-emerald-400/60':getSegStoryboardStatus(si)==='running'?'text-violet-400/60':'text-white/20'">
                {{ getSegStoryboardStatus(si)==='completed'?'✓':getSegStoryboardStatus(si)==='running'?'...':'✗' }}
              </span>
              <button @click.stop="generateSingleStoryboard(si)" class="px-1.5 py-0.5 bg-[#7c3aed] hover:bg-[#6d28d9] rounded text-[8px] font-medium shrink-0" :disabled="isSegStoryboardGenerating(si)">{{ isSegStoryboardGenerating(si)?'...':'故事板' }}</button>
              <button @click.stop="confirmDeleteSegment(si)" class="text-white/15 hover:text-red-400 text-[9px] shrink-0">x</button>
            </div>
            <!-- 展开内容 -->
            <div v-if="seg._open" class="px-2 pb-2 space-y-1 border-t border-white/[0.03]">
              <!-- 引用资产 -->
              <div class="pt-1.5 flex items-center gap-1 flex-wrap">
                <span class="text-[8px] text-white/15">引用:</span>
                <label v-for="(a, ai) in editAssets" :key="'ref'+ai" class="flex items-center gap-0.5 cursor-pointer">
                  <input type="checkbox" :value="ai" v-model="seg.assets" class="w-2 h-2 accent-violet-500" />
                  <span class="text-[8px] text-white/25">{{ a.name || '资产'+(ai+1) }}</span>
                </label>
                <span v-if="!editAssets.length" class="text-[8px] text-white/15">暂无资产</span>
              </div>
              <!-- 镜头列表 -->
              <div v-for="(sh, shi) in seg.shots" :key="'sh'+shi" class="py-0.5 space-y-0.5">
                <div class="flex items-center gap-1">
                  <span class="text-[8px] text-white/15 w-5 shrink-0">{{ shi+1 }}</span>
                  <input v-model="sh.visual" class="flex-1 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 min-w-0" placeholder="画面" />
                </div>
                <div class="flex items-center gap-1 pl-5">
                  <input v-model="sh.camera" class="w-14 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 shrink-0" placeholder="运镜" />
                  <input v-model="sh.lighting" class="w-14 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 shrink-0" placeholder="光线" />
                  <input v-model="sh.audio" class="w-14 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 shrink-0" placeholder="音效" />
                  <input v-model="sh.dialogue" class="w-16 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 shrink-0" placeholder="台词" />
                  <select v-model="sh.transition" class="w-16 bg-white/[0.02] border border-white/[0.04] rounded px-1 py-0.5 text-[10px] focus:outline-none focus:border-[#7c3aed]/30 shrink-0 text-white/50">
                    <option value="cut">[cut]</option><option value="dissolve">[dissolve]</option><option value="camera_push">[camera_push]</option><option value="camera_pan">[camera_pan]</option><option value="fade_black">[fade_black]</option><option value="end">[end]</option>
                  </select>
                  <button @click="confirmDeleteShot(seg,shi)" class="text-white/10 hover:text-red-400 text-[8px] shrink-0">x</button>
                </div>
              </div>
              <button @click="addShot(seg)" class="text-[9px] text-white/15 hover:text-white/30">+ 镜头</button>
            </div>
          </div>
          <div v-if="!editSegments.length" class="text-center py-6 text-white/15 text-[10px]">暂无分镜段，请先AI拆段</div>
        </div>
      </div>

      <!-- ─── 视频列 ─── -->
      <div class="flex flex-col border-r border-white/[0.04]" :style="{width: assetCollapsed ? '75%' : '55%'}">
        <div class="px-3 py-2 flex items-center justify-between border-b border-white/[0.04]">
          <span class="text-[11px] font-semibold text-white/40 uppercase tracking-wider">视频 ({{videoDoneCount}}/{{editSegments.length}})</span>
          <div class="flex gap-1">
            <button v-if="editSegments.length" @click="generateAllVideos" class="text-[9px] text-violet-400/50 hover:text-violet-300" :disabled="generatingAllVideos">{{ generatingAllVideos?'生成中...':'全部生成' }}</button>
            <button v-if="editSegments.length && videoDoneCount > 0" @click="regenerateAllVideos" class="text-[9px] text-amber-400/50 hover:text-amber-300" :disabled="generatingAllVideos">重新全部生成</button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-for="(seg, si) in editSegments" :key="'v'+si"
               class="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 space-y-1.5">
            <!-- 头部：标题+生成按钮 -->
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium truncate">{{ seg.title || '段'+(si+1) }}</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="getVideoStatus(si)" class="text-[9px]" :class="getVideoStatus(si)==='completed'?'text-emerald-400/60':getVideoStatus(si)==='running'?'text-violet-400/60':'text-white/20'">
                  {{ getVideoStatus(si)==='completed'?'完成':getVideoStatus(si)==='running'?'生成中':getVideoStatus(si)==='failed'?'失败':'—' }}
                </span>
                <button @click="toggleVideoPromptEdit(si)" class="text-[9px] text-white/25 hover:text-white/50">prompt</button>
                <button @click="generateSingleVideo(si)" class="px-1.5 py-0.5 bg-[#7c3aed] hover:bg-[#6d28d9] rounded text-[8px] font-medium" :disabled="isVideoGenerating(si)||generatingVideo">{{ isVideoGenerating(si)||generatingVideo?'...':'生成' }}</button>
              </div>
            </div>
            <!-- 参考图行：横向滚动展示 -->
            <div v-if="getSegStoryboardImage(si) || getSegRefImages(si).length" class="flex gap-1 overflow-x-auto pb-1" style="scrollbar-width:thin;scrollbar-color:rgba(255,255,255,0.1) transparent">
              <div v-if="getSegStoryboardImage(si)" class="h-14 w-14 shrink-0 rounded overflow-hidden border border-white/[0.06]">
                <img :src="getUrl(getSegStoryboardImage(si))" class="h-full w-full object-cover"
                     @mouseenter="showPreview(getSegStoryboardImage(si), $event)" @mouseleave="hidePreview()" @mousemove="showPreview(getSegStoryboardImage(si), $event)" />
              </div>
              <div v-for="(rimg, ri) in getSegRefImages(si)" :key="'ri'+ri" class="h-14 w-14 shrink-0 rounded overflow-hidden border border-white/[0.06]">
                <img :src="getUrl(rimg)" class="h-full w-full object-cover"
                     @mouseenter="showPreview(rimg, $event)" @mouseleave="hidePreview()" @mousemove="showPreview(rimg, $event)" />
              </div>
            </div>
            <!-- 视频播放器 -->
            <template v-if="getVideoUrl(si)">
              <video :src="getUrl(getVideoUrl(si))" class="w-full rounded border border-white/[0.06]" controls preload="metadata"></video>
              <div class="flex items-center justify-between">
                <button @click="downloadVideo(si)" class="text-[9px] text-violet-400/50 hover:text-violet-300">下载</button>
                <button @click="generateSingleVideo(si)" class="text-[9px] text-white/25 hover:text-white/50">重新生成</button>
              </div>
            </template>
            <template v-else-if="isVideoGenerating(si)">
              <div class="aspect-video rounded bg-black/30 border border-white/[0.06] flex items-center justify-center">
                <div class="flex items-center gap-1.5"><div class="dot-spin"></div><span class="text-[10px] text-white/30">生成中</span></div>
              </div>
            </template>
            <template v-else-if="getVideoStatus(si)==='failed'">
              <div class="py-2 text-center"><span class="text-red-400/50 text-[10px]">失败</span> <button @click="retryItem(4,si)" class="text-[10px] text-red-300/50 hover:text-red-300">重试</button></div>
            </template>
            <template v-else>
              <div class="aspect-video rounded bg-black/20 border border-white/[0.04] flex items-center justify-center"><span class="text-[10px] text-white/10">未生成</span></div>
            </template>
            <!-- prompt -->
            <div v-if="getVideoPrompt(si)" class="px-1.5 py-1 bg-black/20 rounded text-[9px] text-white/25 line-clamp-2 cursor-pointer" @click="showPromptDetail(getVideoPrompt(si))">{{ getVideoPrompt(si).slice(0,120) }} ▸</div>
            <!-- prompt编辑区 -->
            <div v-if="editingVideoPrompt===si" class="space-y-1">
              <textarea v-model="videoPromptEdits[si]" class="w-full bg-white/[0.02] border border-white/[0.04] rounded px-2 py-1 text-[10px] text-white/50 focus:outline-none focus:border-[#7c3aed]/30 resize-none" rows="3"></textarea>
              <div class="flex justify-end gap-1">
                <button @click="editingVideoPrompt=-1" class="px-2 py-0.5 text-[9px] text-white/30">取消</button>
                <button @click="generateSingleVideo(si, videoPromptEdits[si])" class="px-2 py-0.5 bg-[#7c3aed] rounded text-[9px] text-white">用此prompt生成</button>
              </div>
            </div>
          </div>
          <div v-if="!editSegments.length" class="text-center py-6 text-white/15 text-[10px]">暂无分镜段，请先AI拆段</div>
        </div>
      </div>

      <!-- ─── Agent面板（右下角浮动） ─── -->
      <!-- 迷你模式 -->
      <div v-if="showAgent && agentMini" @click="agentMini=false" class="fixed bottom-4 right-4 z-50 w-10 h-10 rounded-full flex items-center justify-center cursor-pointer shadow-2xl" style="background:#0d0d16;border:2px solid #7c3aed;box-shadow:0 0 20px rgba(124,58,237,0.3)">
        <div class="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
          <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
        </div>
      </div>
      <!-- 完整模式 -->
      <div v-if="showAgent && !agentMini" class="fixed bottom-4 right-4 z-50 flex flex-col rounded-2xl shadow-2xl" style="width:360px;height:480px;background:#0d0d16;border:2px solid #7c3aed;box-shadow:0 0 20px rgba(124,58,237,0.3),0 0 60px rgba(124,58,237,0.1)">
        <div class="px-3 py-2 border-b border-white/[0.08] flex items-center justify-between shrink-0 rounded-t-2xl" style="background:linear-gradient(135deg,rgba(124,58,237,0.15),rgba(139,92,246,0.08))">
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              <svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            </div>
            <span class="text-[12px] font-semibold text-white">锤子导演</span>
            <span class="text-[9px] text-violet-400/60">AI Agent</span>
          </div>
          <div class="flex items-center gap-2">
            <button @click="chatHistory=[]" class="text-[10px] text-white/30 hover:text-white/60 transition">清空</button>
            <button @click="agentMini=true" class="text-[10px] text-white/30 hover:text-white/60 transition">—</button>
            <button @click="showAgent=false" class="text-[10px] text-white/30 hover:text-white/60 transition">✕</button>
          </div>
        </div>
        <!-- Chat Messages -->
        <div ref="chatBox" class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="chatHistory.length === 0" class="text-center py-6">
            <div class="w-8 h-8 mx-auto mb-2 rounded-full bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center">
              <svg class="w-4 h-4 text-violet-400/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            </div>
            <p class="text-[12px] text-white/50 mb-1">和锤子导演聊你的剧本</p>
            <p class="text-[10px] text-white/25">粘贴剧本让它拆段，或让它改分镜、加角色</p>
            <div class="mt-3 space-y-1.5">
              <button v-for="q in quickPrompts" :key="q" @click="chatInput=q;sendChat()" class="block w-full text-left px-3 py-2 rounded-lg text-[12px] text-white/45 hover:text-white/80 transition" style="background:#181826;border:1px solid #2e2e42">
                {{ q }}
              </button>
            </div>
          </div>
          <div v-for="(msg, i) in chatHistory" :key="'m'+i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
            <div class="max-w-[85%] rounded-xl px-3 py-2 text-[12px] leading-relaxed"
              :class="msg.role === 'user' ? 'text-violet-200' : 'text-white/70'"
              :style="msg.role === 'user' ? 'background:rgba(124,58,237,0.3)' : 'background:#181826'">
              <div v-if="msg.role === 'assistant' && msg.actions?.length" class="mb-1 flex gap-1 flex-wrap">
                <span v-for="a in msg.actions" :key="a" class="text-[8px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400/80">{{ a }}</span>
              </div>
              <div class="whitespace-pre-wrap">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="chatLoading" class="flex justify-start">
            <div class="rounded-xl px-3 py-2 flex items-center gap-1.5" style="background:#181826">
              <div class="flex gap-0.5"><span class="w-1.5 h-1.5 bg-violet-400/60 rounded-full animate-bounce" style="animation-delay:0ms"></span><span class="w-1.5 h-1.5 bg-violet-400/60 rounded-full animate-bounce" style="animation-delay:150ms"></span><span class="w-1.5 h-1.5 bg-violet-400/60 rounded-full animate-bounce" style="animation-delay:300ms"></span></div>
              <span class="text-[11px] text-white/40">思考中...</span>
            </div>
          </div>
        </div>
        <!-- Chat Input -->
        <div class="p-3 border-t border-white/[0.08]">
          <div class="flex items-center gap-2 rounded-lg px-3 py-1.5" style="background:#252540 !important;border:2px solid #7c3aed !important;box-shadow:0 0 8px rgba(124,58,237,0.2)">
            <input v-model="chatInput" @keydown.enter="sendChat" class="flex-1 bg-transparent text-[13px] text-white placeholder-white/40 outline-none" placeholder="输入消息..." :disabled="chatLoading" />
            <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()" class="shrink-0 w-8 h-8 flex items-center justify-center rounded-md text-white disabled:opacity-30 transition" style="background:#7c3aed !important">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ═══ 剧本弹窗 ═══ -->
  <div v-if="scriptModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" @click.self="scriptModal=false">
    <div class="bg-[#0d0d14] border border-white/[0.06] rounded-2xl p-5 w-full max-w-2xl">
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm font-semibold">剧本</span>
        <button @click="scriptModal=false" class="text-white/30 hover:text-white text-xs">x</button>
      </div>
      <textarea v-model="rawScript" class="w-full bg-white/[0.02] border border-white/[0.04] rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-[#7c3aed]/30 resize-none" rows="10" placeholder="粘贴剧本..."></textarea>
      <div class="flex items-center gap-2 mt-3">
        <label class="px-3 py-1.5 bg-white/[0.06] hover:bg-white/[0.1] rounded-lg text-xs cursor-pointer">
          上传txt
          <input type="file" accept=".txt,.md,.text" class="hidden" @change="uploadScriptDetail" />
        </label>
        <div class="flex-1"></div>
        <button @click="saveRawScript(); scriptModal=false" class="px-3 py-1.5 bg-white/[0.06] hover:bg-white/[0.1] rounded-lg text-xs" :disabled="!rawScript.trim()">保存</button>
        <button @click="aiSplit(); scriptModal=false" class="px-3 py-1.5 bg-[#7c3aed] hover:bg-[#6d28d9] rounded-lg text-xs font-medium" :disabled="aiSplitting">{{ aiSplitting ? '拆段中...' : 'AI拆段' }}</button>
      </div>
    </div>
  </div>

  <!-- ═══ 视频播放弹窗 ═══ -->
  <div v-if="playingVideoUrl" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-8" @click.self="playingVideoUrl=''">
    <video :src="playingVideoUrl" class="max-w-full max-h-full rounded-lg" controls autoplay></video>
  </div>

  <!-- ═══ Prompt详情弹窗 ═══ -->
  <div v-if="promptDetailText" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="promptDetailText=''">
    <div class="bg-[#12121a] border border-white/[0.06] rounded-2xl p-5 w-full max-w-lg max-h-[60vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-semibold">Prompt详情</span>
        <button @click="promptDetailText=''" class="text-white/30 hover:text-white transition">x</button>
      </div>
      <pre class="text-[11px] text-white/60 whitespace-pre-wrap break-words">{{ promptDetailText }}</pre>
    </div>
  </div>

  <!-- ═══ 图片预览浮层 ═══ -->
  <div v-if="previewImg" class="fixed z-[9999] pointer-events-none" :style="{left: previewPos.x+'px', top: previewPos.y+'px'}">
    <img :src="getUrl(previewImg)" class="max-w-[55vw] max-h-[70vh] object-contain rounded-lg shadow-2xl border border-white/10 bg-black/90" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onActivated, onDeactivated, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { get, post, del, put } from '@/api'

const auth = useAuthStore()
const projects = ref<any[]>([])
const loading = ref(true)
const showCreate = ref(false)
const creating = ref(false)
const savingScript = ref(false)
const proj = ref<any>(null)
const showAgent = ref(true)
const agentMini = ref(false)
const assetCollapsed = ref(false)
const editAssets = ref<any[]>([])
const editSegments = ref<any[]>([])
const rawScript = ref('')
const scriptModal = ref(false)
const aiSplitting = ref(false)
const chatHistory = ref<{role:string,content:string,actions?:string[]}[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBox = ref<HTMLElement|null>(null)
const assetFileInputs = ref<Record<number, any>>({})
const editingVideoPrompt = ref(-1)
const expandedAsset = ref(-1)
const videoPromptEdits = ref<Record<number, string>>({})
const promptDetailText = ref('')
const playingVideoUrl = ref('')
const saveNotification = ref('')
let pollTimer: any = null
// 生成锁，防止重复点击
const generatingAsset = ref(false)
const generatingAllAssets = ref(false)
const generatingVideo = ref(false)
const generatingAllVideos = ref(false)
const generatingStoryboard = ref(false)
const generatingAllStoryboards = ref(false)

// ── 图片预览浮层 ──
const previewImg = ref('')
const previewPos = ref({x:0, y:0})

function showPreview(url: string, e: MouseEvent) {
  if (!url) return
  previewImg.value = url
  const maxW = window.innerWidth * 0.55
  const maxH = window.innerHeight * 0.7
  const x = Math.min(e.clientX + 20, window.innerWidth - maxW - 20)
  const y = Math.min(e.clientY + 20, window.innerHeight - maxH - 20)
  previewPos.value = {x: Math.max(10, x), y: Math.max(10, y)}
}
function hidePreview() {
  previewImg.value = ''
}

const quickPrompts = [
  '帮我拆段这个剧本',
  '给第一个段加一个特写镜头',
  '把运镜改成更有电影感的',
  '帮我加一个反派角色',
]

const createForm = ref({ name:'', video_model:'Gemini Omni', image_model:'GPT-Image2', ratio:'16:9', resolution:'720p', image_resolution:'1K', duration:10, raw_script:'' })

// ── Computed ──

const videoDoneCount = computed(() => {
  if (!editSegments.value.length) return 0
  let count = 0
  for (let i = 0; i < editSegments.value.length; i++) {
    if (getVideoStatus(i) === 'completed') count++
  }
  return count
})

const workflowSteps = computed(() => {
  const p = proj.value
  if (!p) return []
  // Step 1: 剧本 → done when raw_script exists AND segments.length > 0
  const step1Done = !!(p.raw_script && p.segments?.length > 0)
  const step1Running = aiSplitting.value
  // Step 2: 资产生图 → done when all assets have phase2 results with status=completed
  const assets = p.assets || []
  const phase2 = p.results?.phase2 || []
  const step2Done = assets.length > 0 && phase2.length >= assets.length && phase2.every((x: any) => x.status === 'completed')
  const step2Running = phase2.some((x: any) => x.status === 'running')
  // Step 3: 故事板 → done when all segments have phase3 results with status=completed
  const segs = p.segments || []
  const phase3 = p.results?.phase3 || []
  const step3Done = segs.length > 0 && phase3.length >= segs.length && phase3.every((x: any) => x.status === 'completed')
  const step3Running = phase3.some((x: any) => x.status === 'running')
  // Step 4: 视频 → done when all segments have phase4 results with status=completed
  const phase4 = p.results?.phase4 || []
  const step4Done = segs.length > 0 && phase4.length >= segs.length && phase4.every((x: any) => x.status === 'completed')
  const step4Running = phase4.some((x: any) => x.status === 'running')

  return [
    { label: '剧本', status: step1Done ? 'done' : step1Running ? 'running' : 'pending', action: step1Done ? '' : 'AI拆段', actionFn: () => { scriptModal.value = true }, actionDisabled: aiSplitting.value },
    { label: '资产生图', status: step2Done ? 'done' : step2Running ? 'running' : 'pending', action: step2Done ? '' : '全部生成', actionFn: generateAllAssets, actionDisabled: generatingAllAssets.value },
    { label: '故事板', status: step3Done ? 'done' : step3Running ? 'running' : 'pending', action: step3Done ? '' : '全部生图', actionFn: generateAllStoryboards, actionDisabled: generatingAllStoryboards.value },
    { label: '视频', status: step4Done ? 'done' : step4Running ? 'running' : 'pending', action: step4Done ? '' : '全部生成', actionFn: generateAllVideos, actionDisabled: generatingAllVideos.value },
  ]
})

// ── Helper functions ──

function phaseLabel(p:number){return['未开始','AI拆段','资产生图','故事板生图','视频生成'][p]||'未开始'}
function phaseClass(p:number){if(p===0)return'bg-white/[0.06] text-white/30';if(p===4)return'bg-emerald-500/15 text-emerald-400/70';return'bg-violet-500/15 text-violet-400/70'}
function phaseBorderClass(p:number){const r=proj.value?.results?.[`phase${p}`]||[];if(r.some((x:any)=>x.status==='running'))return'border-violet-500/20 bg-violet-500/[0.02]';if(r.length>0&&r.every((x:any)=>['completed','failed','timeout'].includes(x.status)))return'border-emerald-500/15 bg-emerald-500/[0.01]';return'border-white/[0.04] bg-white/[0.01]'}
function canRunPhase(p:number){if(!proj.value)return false;const r=proj.value.results?.[`phase${p}`]||[];if(!r.length)return true;return r.some((x:any)=>!['completed','failed','timeout'].includes(x.status))}
function isPhaseRunning(p:number){if(!proj.value)return false;return(proj.value.results?.[`phase${p}`]||[]).some((x:any)=>x.status==='running')}
function isPhaseDone(p:number){if(!proj.value)return false;const r=proj.value.results?.[`phase${p}`]||[];return r.length>0&&r.every((x:any)=>['completed','failed','timeout'].includes(x.status))}
function getUrl(url:string){if(!url)return'';const t=localStorage.getItem('aiforge_token');if(url.startsWith('/api/')){const s=url.includes('?')?'&':'?';return t?`${url}${s}token=${t}`:url}return url}
function addShot(seg:any){if(!seg.shots)seg.shots=[];seg.shots.push({visual:'',camera:'',dialogue:'',lighting:'',audio:'',transition:'cut'})}
function addSegment(){editSegments.value.push({title:'',shots:[{visual:'',camera:'',dialogue:'',lighting:'',audio:'',transition:'cut'}],_open:true,assets:[]})}
function addAsset(){editAssets.value.push({name:'',type:'角色',prompt:'',reference_image:'',is_primary:true,reference_form:''})}
function getPrimaryCharacters(excludeIndex:number){return editAssets.value.filter((a:any,i:number)=>i!==excludeIndex&&a.type==='角色'&&a.is_primary!==false)}
function parseRefImages(ref:any):string[]{if(!ref)return[];if(Array.isArray(ref))return ref;try{return JSON.parse(ref)}catch{return[]}}
function showPromptDetail(text:string){promptDetailText.value=text}
function playVideo(si:number){playingVideoUrl.value=getUrl(getVideoUrl(si))}

// ── Asset functions ──

function getAssetImage(i:number):string{if(!proj.value?.results?.phase2?.[i]?.result_url)return'';return proj.value.results.phase2[i].result_url}
function getAssetResultImage(i:number):string{return proj.value?.results?.phase2?.[i]?.result_url||''}
function getAssetPrompt(i:number):string{return proj.value?.results?.phase2?.[i]?.prompt||''}
function isAssetGenerating(i:number):boolean{return proj.value?.results?.phase2?.[i]?.status==='running'}

function handleAssetImageClick(i:number){
  const a = editAssets.value[i]
  if(a?.reference_image || getAssetResultImage(i)) return
  uploadAssetRef(i)
}

async function generateSingleAsset(i:number){
  if(!proj.value||generatingAsset.value)return
  generatingAsset.value=true
  try{
    await post(`/project/${proj.value.id}/asset/${i}/generate`,{})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingAsset.value=false
}

async function generateAllAssets(){
  if(!proj.value||generatingAllAssets.value)return
  generatingAllAssets.value=true
  for(let i=0;i<editAssets.value.length;i++){
    if(!isAssetGenerating(i)&&!getAssetResultImage(i)){
      try{await post(`/project/${proj.value.id}/asset/${i}/generate`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllAssets.value=false
}

function uploadAssetRef(i:number){
  const el=assetFileInputs.value[i] as HTMLInputElement|null
  el?.click()
}

async function handleAssetRefUpload(e:Event,i:number){
  const file=(e.target as HTMLInputElement).files?.[0]
  if(!file)return
  try{
    const formData=new FormData()
    formData.append('file',file)
    const res:any=await post('/gen/upload',formData)
    if(res.url){
      await post(`/project/${proj.value!.id}/asset/${i}/reference`,{image_url:res.url})
      editAssets.value[i].reference_image=res.url
      proj.value=await get(`/project/${proj.value!.id}`)
    }
  }catch(e:any){alert(e.message||'上传失败')}
}

function uploadAssetResult(i:number){
  const input=document.createElement('input')
  input.type='file'
  input.accept='image/*'
  input.onchange=async(e:Event)=>{
    const file=(e.target as HTMLInputElement).files?.[0]
    if(!file)return
    try{
      const formData=new FormData()
      formData.append('file',file)
      const res:any=await post('/gen/upload',formData)
      if(res.url){
        await post(`/project/${proj.value!.id}/asset/${i}/upload-result`,{image_url:res.url})
        proj.value=await get(`/project/${proj.value!.id}`)
      }
    }catch(e2:any){alert(e2.message||'上传失败')}
  }
  input.click()
}

// ── Storyboard functions ──

function getSegStoryboardImage(i:number):string{return proj.value?.results?.phase3?.[i]?.result_url||''}
function isSegStoryboardGenerating(i:number):boolean{return proj.value?.results?.phase3?.[i]?.status==='running'}
function getSegStoryboardStatus(i:number):string{return proj.value?.results?.phase3?.[i]?.status||''}

async function generateSingleStoryboard(i:number){
  if(!proj.value||generatingStoryboard.value)return
  generatingStoryboard.value=true
  try{
    await post(`/project/${proj.value.id}/segment/${i}/generate-storyboard`,{})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingStoryboard.value=false
}

async function generateAllStoryboards(){
  if(!proj.value||generatingAllStoryboards.value)return
  generatingAllStoryboards.value=true
  for(let i=0;i<editSegments.value.length;i++){
    if(!isSegStoryboardGenerating(i)&&!getSegStoryboardImage(i)){
      try{await post(`/project/${proj.value.id}/segment/${i}/generate-storyboard`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllStoryboards.value=false
}

// ── Video functions ──

function videoResults(){return proj.value?.results?.phase4||[]}
function getVideoUrl(i:number):string{return videoResults()[i]?.result_url||''}
function getVideoStatus(i:number):string{return videoResults()[i]?.status||''}
function getVideoPrompt(i:number):string{return videoResults()[i]?.prompt||''}
function isVideoGenerating(i:number):boolean{return videoResults()[i]?.status==='running'}
function getSegRefImages(i:number):string[]{
  const ref=videoResults()[i]?.reference_images
  if(!ref)return[]
  try{return JSON.parse(ref)}catch{return[]}
}

async function generateSingleVideo(i:number,customPrompt?:string){
  if(!proj.value||generatingVideo.value)return
  generatingVideo.value=true
  try{
    await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{prompt:customPrompt||null})
    proj.value=await get(`/project/${proj.value.id}`)
    startPolling()
  }catch(e:any){alert(e.message||'生成失败')}
  generatingVideo.value=false
}

async function generateAllVideos(){
  if(!proj.value||generatingAllVideos.value)return
  generatingAllVideos.value=true
  for(let i=0;i<editSegments.value.length;i++){
    if(!isVideoGenerating(i)&&getVideoStatus(i)!=='completed'){
      try{await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{})}catch(e:any){console.error(e)}
    }
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllVideos.value=false
}

async function regenerateAllVideos(){
  if(!proj.value||generatingAllVideos.value)return
  if(!confirm('确定重新生成所有视频？将消耗积分'))return
  generatingAllVideos.value=true
  for(let i=0;i<editSegments.value.length;i++){
    try{await post(`/project/${proj.value.id}/segment/${i}/generate-video`,{})}catch(e:any){console.error(e)}
  }
  proj.value=await get(`/project/${proj.value.id}`)
  startPolling()
  generatingAllVideos.value=false
}

function toggleVideoPromptEdit(i:number){
  if(editingVideoPrompt.value===i){
    editingVideoPrompt.value=-1
  }else{
    editingVideoPrompt.value=i
    videoPromptEdits.value[i]=getVideoPrompt(i)||''
  }
}

function downloadVideo(si:number){
  if(!proj.value)return
  const url=getVideoUrl(si)
  if(!url)return
  window.open(getUrl(url),'_blank')
}

// ── Project CRUD ──

async function fetchProjects(){loading.value=true;try{projects.value=await get('/project/list')}catch(e){console.error(e)};loading.value=false}

async function createProject(){creating.value=true;try{const res:any=await post('/project/create',{...createForm.value,script:JSON.stringify({assets:[],segments:[]})});showCreate.value=false;const newRawScript=createForm.value.raw_script;createForm.value={name:'',video_model:'Gemini Omni',image_model:'GPT-Image2',ratio:'16:9',resolution:'720p',image_resolution:'1K',duration:10,raw_script:''};await fetchProjects();editAssets.value=[];editSegments.value=[];chatHistory.value=[];const newId=res?.id;if(newId){await openProject({id:newId})}else if(projects.value.length){await openProject(projects.value[0])}if(newRawScript.trim()){rawScript.value=newRawScript;scriptModal.value=true}}catch(e:any){alert(e.message||'创建失败')};creating.value=false}

function uploadScript(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{createForm.value.raw_script=r.result as string};r.readAsText(f)}
function uploadScriptDetail(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{rawScript.value=r.result as string};r.readAsText(f)}

async function saveRawScript(){if(!proj.value||!rawScript.value.trim())return;try{await put(`/project/${proj.value.id}/raw-script`,{raw_script:rawScript.value});proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'保存失败')}}

async function openProject(p:any){try{proj.value=await get(`/project/${p.id}`);editAssets.value=proj.value.assets?.length?JSON.parse(JSON.stringify(proj.value.assets)).map((a:any)=>({...a,is_primary:a.type==='角色'?(a.is_primary!==false):undefined,reference_form:a.type==='角色'?(a.reference_form||''):undefined})):[];editSegments.value=proj.value.segments?.length?JSON.parse(JSON.stringify(proj.value.segments)).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]})):[];rawScript.value=proj.value.raw_script||'';scriptModal.value=false;try{const chatRes:any=await get(`/project/${p.id}/chat-history`);chatHistory.value=chatRes.history||[]}catch{chatHistory.value=[]}startPolling()}catch(e){console.error(e)}}
function closeProject(){proj.value=null;stopPolling();editAssets.value=[];editSegments.value=[];chatHistory.value=[]}

function startPolling(){stopPolling();pollTimer=setInterval(async()=>{if(!proj.value){stopPolling();return}const r=proj.value.results||{};if(!['phase2','phase3','phase4'].some(k=>(r[k]||[]).some((x:any)=>x.status==='running'||x.status==='pending'))){stopPolling();return}try{proj.value=await get(`/project/${proj.value.id}`)}catch(e){console.error(e)}},5000)}
function stopPolling(){if(pollTimer){clearInterval(pollTimer);pollTimer=null}}

async function saveScript(){if(!proj.value)return;savingScript.value=true;try{const prevResults=proj.value.results||{};const prevPhase2Count=(prevResults.phase2||[]).filter((x:any)=>x.status==='completed').length;const prevPhase3Count=(prevResults.phase3||[]).filter((x:any)=>x.status==='completed').length;const prevPhase4Count=(prevResults.phase4||[]).filter((x:any)=>x.status==='completed').length;const d={assets:editAssets.value.map(a=>({name:a.name,type:a.type,prompt:a.prompt,reference_image:a.reference_image,is_primary:a.type==='角色'?a.is_primary:undefined,reference_form:a.type==='角色'&&!a.is_primary?a.reference_form:undefined})),segments:editSegments.value.map(s=>{const{_open,...rest}=s;return rest})};await put(`/project/${proj.value.id}/script`,{script:JSON.stringify(d)});proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();const newResults=proj.value.results||{};const newPhase2Count=(newResults.phase2||[]).filter((x:any)=>x.status==='completed').length;const newPhase3Count=(newResults.phase3||[]).filter((x:any)=>x.status==='completed').length;const newPhase4Count=(newResults.phase4||[]).filter((x:any)=>x.status==='completed').length;const clearedAssets=prevPhase2Count-newPhase2Count;const clearedStoryboards=prevPhase3Count-newPhase3Count;const clearedVideos=prevPhase4Count-newPhase4Count;const parts=[];if(clearedAssets>0)parts.push(`${clearedAssets}个资产`);if(clearedStoryboards>0)parts.push(`${clearedStoryboards}个故事板`);if(clearedVideos>0)parts.push(`${clearedVideos}段视频`);if(parts.length>0){saveNotification.value=`已保存，${parts.join('和')}需要重新生成`;setTimeout(()=>{saveNotification.value=''},4000)}else{saveNotification.value='已保存';setTimeout(()=>{saveNotification.value=''},2000)}}catch(e:any){alert(e.message||'保存失败')};savingScript.value=false}

async function aiSplit(){if(!proj.value)return;aiSplitting.value=true;try{const res:any=await post(`/project/${proj.value.id}/ai-split`,{duration_per_segment:proj.value.duration||10});editAssets.value=res.assets||[];editSegments.value=(res.segments||[]).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]}));proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();await auth.fetchProfile();chatHistory.value.push({role:'assistant',content:`已拆段完成：${res.assets_count}个资产，${res.segments_count}段分镜。你可以在「资产」区查看和调整。`,actions:['update_script']})}catch(e:any){alert(e.message||'AI拆段失败')};aiSplitting.value=false}

async function sendChat(){if(!proj.value||!chatInput.value.trim()||chatLoading.value)return;const msg=chatInput.value;chatInput.value='';chatHistory.value.push({role:'user',content:msg});chatLoading.value=true;await nextTick();scrollChat();try{const res:any=await post(`/project/${proj.value.id}/chat`,{message:msg,history:chatHistory.value.slice(-20).map(m=>({role:m.role,content:m.content}))});const toolNames=res.tool_results?.length?res.tool_results.map((t:any)=>t.tool):[];chatHistory.value.push({role:'assistant',content:res.reply,actions:toolNames.length?toolNames:undefined});if(res.script_modified){editAssets.value=res.assets||[];editSegments.value=(res.segments||[]).map((s:any)=>({...s,_open:false,assets:s.assets||s.referenced_assets||[]}));proj.value=await get(`/project/${proj.value.id}`);await fetchProjects()}await auth.fetchProfile()}catch(e:any){chatHistory.value.push({role:'assistant',content:`出错了: ${e.message||'未知错误'}`})}chatLoading.value=false;await nextTick();scrollChat()}
function scrollChat(){if(chatBox.value)chatBox.value.scrollTop=chatBox.value.scrollHeight}

async function runPhase(phase:number){if(!proj.value)return;try{await post(`/project/${proj.value.id}/run`,{phase});proj.value=await get(`/project/${proj.value.id}`);await fetchProjects();await auth.fetchProfile();startPolling()}catch(e:any){alert(e.message||'执行失败')}}
async function retryItem(phase:number,index:number){if(!proj.value)return;try{await post(`/project/${proj.value.id}/retry/${phase}/${index}`,{});proj.value=await get(`/project/${proj.value.id}`);await auth.fetchProfile();startPolling()}catch(e:any){alert(e.message||'重试失败')}}
function downloadPhase(phase:number){if(!proj.value)return;const t=localStorage.getItem('aiforge_token');const u=`/api/project/${proj.value.id}/download/${phase}${t?`?token=${t}`:''}`;const a=document.createElement('a');a.href=u;a.download='';document.body.appendChild(a);a.click();document.body.removeChild(a)}
async function confirmDeleteAsset(i:number){if(!confirm('确定删除该资产？'))return;try{await del(`/project/${proj.value.id}/asset/${i}`);editAssets.value.splice(i,1);proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'删除失败')}}
async function confirmDeleteSegment(si:number){if(!confirm('确定删除该段分镜？'))return;try{await del(`/project/${proj.value.id}/segment/${si}`);editSegments.value.splice(si,1);proj.value=await get(`/project/${proj.value.id}`)}catch(e:any){alert(e.message||'删除失败')}}
function confirmDeleteShot(seg:any,shi:number){if(!confirm('确定删除该镜头？'))return;seg.shots.splice(shi,1)}
function confirmRunPhase(phase:number){const labels={2:'资产生图',3:'故事板生图',4:'生成视频'};if(!confirm(`确定执行「${labels[phase]||'Phase'+phase}」？将消耗积分`))return;runPhase(phase)}
async function deleteProject(){if(!proj.value||!confirm('确定删除？'))return;try{await del(`/project/${proj.value.id}`);proj.value=null;stopPolling();await fetchProjects()}catch(e){console.error(e)}}

onMounted(fetchProjects)
onActivated(() => { fetchProjects() })
onDeactivated(() => { stopPolling() })
onUnmounted(() => { stopPolling() })
</script>

<style scoped>
.lbl{@apply block text-[11px] text-white/70 mb-1}
.inp{@apply w-full bg-white/[0.06] border border-white/[0.1] rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-[#7c3aed]/50 transition}
.sel{@apply w-full bg-white/[0.06] border border-white/[0.1] rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-[#7c3aed]/50 transition}
.dot-spin{@apply w-3 h-3 border-[1.5px] border-violet-500/40 border-t-transparent rounded-full animate-spin}
.line-clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.writing-vertical{writing-mode:vertical-rl}
</style>
