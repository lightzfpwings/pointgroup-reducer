/* 文案显式翻译；偏好持久化失败时仍可完整使用计算功能。 */
(function(root){
  'use strict';
  const messages=typeof module!=='undefined'&&module.exports?require('./messages-data.js'):root.I18nMessages;
  const languages=['zh-Hans','zh-Hant','en'];let current='zh-Hans';const listeners=[];
  try{const preferred=root.BasisPreferredLanguage||root.localStorage?.getItem('symmetry-language')||root.BasisDefaultLanguage;if(languages.includes(preferred))current=preferred;}catch(_){if(languages.includes(root.BasisDefaultLanguage))current=root.BasisDefaultLanguage;}
  const sorted=Object.keys(messages).sort((a,b)=>b.length-a.length);
  function translate(text){text=String(text);if(current==='zh-Hans')return text;const col=current==='en'?1:0;if(messages[text])return messages[text][col];
    // 动态文本只翻译已登记的片段，数值、函数标识及用户自定义文本保持原样。
    let offset=0,out='';while(offset<text.length){const key=sorted.find(k=>text.startsWith(k,offset));if(key){out+=messages[key][col];offset+=key.length;}else out+=text[offset++];}return out;
  }
  function canonical(text){text=String(text);if(current==='zh-Hans')return text;const col=current==='en'?1:0;const keys=sorted.filter(k=>/[\u4e00-\u9fff]/.test(k)).sort((a,b)=>messages[b][col].length-messages[a][col].length);
    let offset=0,out='';while(offset<text.length){const key=keys.find(k=>messages[k][col]&&text.startsWith(messages[k][col],offset));if(key){out+=key;offset+=messages[key][col].length;}else out+=text[offset++];}return out;
  }
  function apply(doc){
    doc.documentElement.lang=current==='en'?'en':current==='zh-Hant'?'zh-Hant':'zh-Hans';doc.title=translate('点群与基函数');
    doc.querySelectorAll('[data-i18n]').forEach(n=>n.textContent=translate(n.getAttribute('data-i18n')));
    for(const attr of ['title','placeholder','aria-label'])doc.querySelectorAll('[data-i18n-'+attr+']').forEach(n=>n.setAttribute(attr,translate(n.getAttribute('data-i18n-'+attr))));
  }
  function setLanguage(value){if(!languages.includes(value))return false;current=value;
    try{root.localStorage?.setItem('symmetry-language',value);}catch(_){}
    const bridge=root.webkit?.messageHandlers?.languageChanged;if(bridge)bridge.postMessage({language:value});
    listeners.forEach(fn=>fn(value));return true;
  }
  const errors={
    invalid_json:['JSON 格式无效，请检查输入文件。','JSON 格式無效，請檢查輸入檔案。','Invalid JSON. Check the input file.'],
    invalid_expression:['无效的数值表达式。','無效的數值運算式。','Invalid numeric expression.'],
    expression_limit:['表达式过长或复杂度超限。','運算式過長或複雜度超限。','Expression length or complexity limit exceeded.'],
    character_count:['特征标数量不符，请按当前表每类输入一个。','特徵標數量不符，請依目前表格每類輸入一個。','Incorrect character count. Enter one value per class.'],
    nonfinite_characters:['特征标必须是有限数。','特徵標必須是有限數。','Characters must be finite numbers.'],
    invalid_reduction_tolerance:['约化容差必须大于 0 且小于 0.01。','約化容差必須大於 0 且小於 0.01。','Reduction tolerance must be greater than 0 and less than 0.01.'],
    unsupported_reducer_group:['不支持此约化点群。','不支援此約化點群。','Unsupported reduction point group.'],
    table_shape:['特征标表维数不符。','特徵標表維數不符。','Character table shape mismatch.'],
    table_orthogonality:['特征标表未通过正交性检查。','特徵標表未通過正交性檢查。','Character table orthogonality check failed.'],
    integration_invalid:['基函数特征标未通过约化检查。','基函數特徵標未通過約化檢查。','Basis characters failed reduction checks.'],
    integration_sum:['各块重数之和与全体重数不符。','各塊重數之和與全體重數不符。','Block multiplicities do not sum to the total.'],
    unsupported_group:['该点群暂未提供真实空间操作。','此點群暫未提供真實空間操作。','Spatial operations are not available for this group.'],
    basis_not_closed:['所选基函数不封闭，请补齐变换产生的分量。','所選基函數不封閉，請補齊變換產生的分量。','Basis is not closed. Add the components produced by the transformation.'],
    dependent_basis:['同中心、同径向类型的函数线性相关。','同中心、同徑向類型的函數線性相關。','Functions at one site with the same radial type are linearly dependent.'],
    invalid_frame:['局部轴必须构成单位正交的右手坐标系。','局部軸必須構成單位正交的右手座標系。','Local axes must form an orthonormal right-handed frame.'],
    invalid_d_component:['请选择五个实球谐 d 分量之一。','請選擇五個實球諧 d 分量之一。','Choose one of the five real d harmonics.'],
    missing_site:['操作后缺少同类型的目标中心。','操作後缺少同類型的目標中心。','A symmetry operation has no matching target site of the same type.'],
    ambiguous_mapping:['操作后对应多个目标中心，请减小容差。','操作後對應多個目標中心，請縮小容差。','Multiple target sites match. Reduce the tolerance.'],
    ambiguous_orbit:['位置去重存在多个候选，请减小容差。','位置去重存在多個候選，請縮小容差。','Orbit deduplication is ambiguous. Reduce the tolerance.'],
    orbit_stabilizer:['展开数量与稳定子不符，请调整坐标或容差。','展開數量與穩定子不符，請調整座標或容差。','Orbit size and stabilizer disagree. Adjust coordinates or tolerance.'],
    invalid_vector:['坐标或方向必须是三个有限数。','座標或方向必須是三個有限數。','A coordinate or direction must contain three finite numbers.'],
    invalid_tolerance:['位置容差须在 1e−10 至 0.01 之间。','位置容差須在 1e−10 至 0.01 之間。','Position tolerance must be between 1e−10 and 0.01.'],
    site_count:['中心数量须为 1 至 120。','中心數量須為 1 至 120。','Use 1 to 120 sites.'],
    site_id:['中心编号须唯一且非空。','中心編號須唯一且非空。','Site IDs must be unique and nonempty.'],
    site_kind:['中心需要元素或等价类型。','中心需要元素或等價類型。','Each site needs an element or equivalence type.'],
    coincident_sites:['中心坐标重合，请让轨道引用同一中心。','中心座標重合，請讓軌道引用同一中心。','Coincident sites. Orbitals should share a single site.'],
    function_count:['独立基函数数量须为 1 至 180。','獨立基函數數量須為 1 至 180。','Use 1 to 180 independent basis functions.'],
    function_id:['基函数编号须唯一且非空。','基函數編號須唯一且非空。','Function IDs must be unique and nonempty.'],
    unknown_site:['基函数引用的中心不存在。','基函數引用的中心不存在。','A basis function refers to an unknown site.'],
    missing_radial:['基函数需要径向副本标识。','基函數需要徑向副本識別碼。','Each basis function needs a radial copy identifier.'],
    unsupported_family:['支持 s、p 和五维实球谐 d。','支援 s、p 及五維實球諧 d。','Supported families are s, p and five real d harmonics.'],
    zero_direction:['p 方向不能为零向量。','p 方向不能為零向量。','p direction cannot be a zero vector.'],
    representation_relation:['基函数变换未通过群关系检查。','基函數變換未通過群關係檢查。','Basis transformations failed the group relation checks.'],
    class_trace:['同一共轭类的特征标不一致。','同一共軛類的特徵標不一致。','Characters are inconsistent within a conjugacy class.'],
    dimension_check:['单位操作的特征标与维数不符。','單位操作的特徵標與維數不符。','The identity character differs from the dimension.'],
    invalid_spec:['输入项目格式有误。','輸入專案格式有誤。','Invalid project input.'],
    template:['未知示例。','未知範例。','Unknown example.']
  };
  for(const code of ['group_limit','group_size','group_closure','group_orthogonal','group_inverse','operation_label','mapping_bijection'])errors[code]=['空间群操作校验失败。','空間群操作驗證失敗。','Spatial group operation validation failed.'];
  Object.values(errors).forEach(([cn,tw,en])=>{if(!messages[cn]){messages[cn]=[tw,en];sorted.push(cn);}});sorted.sort((a,b)=>b.length-a.length);
  function error(e){
    if(e?.name==='SyntaxError')return errors.invalid_json[current==='en'?2:current==='zh-Hant'?1:0];
    if(e&&errors[e.code]&&(current!=='zh-Hans'||e.name==='ReductionError')){
      const message=errors[e.code][current==='en'?2:current==='zh-Hant'?1:0],d=e.detail||{};
      return message+(d.function?' ['+d.function+']':'')+(d.site?' ['+d.site+']':'')+(d.operation!==undefined?' [g'+d.operation+']':'')+(d.expected?' ('+d.expected+')':'');
    }
    return translate(e?.message||String(e));
  }
  const api={translate,canonical,apply,setLanguage,language:()=>current,onChange:fn=>listeners.push(fn),languages,error,messages};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;root.I18n=api;
})(typeof globalThis!=='undefined'?globalThis:this);
